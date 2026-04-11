# attendance/face_utils.py

import os
import logging
from pathlib import Path
import numpy as np
import cv2

from django.conf import settings
from deepface import DeepFace
from students.models import Student

logger = logging.getLogger('face_recognition')

ENC_DIR = Path(settings.MEDIA_ROOT) / "encodings_deepface"
MODEL_NAME = "Facenet"
DIST_THRESHOLD = 0.65


def _ensure_dir():
    """Ensure encoding directory exists and is writable."""
    try:
        ENC_DIR.mkdir(parents=True, exist_ok=True)
        if not os.access(ENC_DIR, os.W_OK):
            logger.error(f"Encoding directory not writable: {ENC_DIR}")
            return False
        logger.debug(f"Encoding directory ready: {ENC_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create encoding directory: {e}")
        return False


def build_embedding_for_student(student):
    """
    Build and save DeepFace embedding for a student.
    Returns True if successful, False otherwise.
    """
    try:
        if not student.photo:
            logger.warning(f"Student {student.id} ({student.name}) has no photo")
            return False

        if not _ensure_dir():
            logger.error(f"Cannot proceed with encoding for student {student.id}")
            return False

        img_path = str(student.photo.path)
        
        if not os.path.exists(img_path):
            logger.error(f"Photo file not found for student {student.id}: {img_path}")
            return False

        logger.debug(f"Building embedding for student {student.id}: {img_path}")

        # DeepFace.represent returns list of dicts
        objs = DeepFace.represent(
            img_path=img_path,
            model_name=MODEL_NAME,
            enforce_detection=False
        )

        if not objs:
            logger.warning(f"No embedding generated for student {student.id}")
            return False

        embedding = np.array(objs[0]["embedding"], dtype=np.float32)
        enc_file = ENC_DIR / f"student_{student.id}_{MODEL_NAME}.npy"
        np.save(str(enc_file), embedding)
        logger.info(f"Successfully saved encoding for student {student.id}: {student.name}")
        return True

    except Exception as e:
        logger.error(f"Exception building embedding for student {student.id}: {e}", exc_info=True)
        return False


def load_known_faces():
    """
    Load all stored embeddings from disk.
    Returns tuple of (known_encodings list, known_ids list)
    """
    try:
        if not _ensure_dir():
            logger.warning("Encoding directory not available, returning empty encodings")
            return [], []

        known_encodings = []
        known_ids = []

        students = Student.objects.all().select_related('classroom')
        
        for student in students:
            enc_file = ENC_DIR / f"student_{student.id}_{MODEL_NAME}.npy"
            if enc_file.exists():
                try:
                    emb = np.load(str(enc_file))
                    known_encodings.append(emb)
                    known_ids.append(student.id)
                except Exception as e:
                    logger.error(f"Failed to load encoding for student {student.id}: {e}")
                    continue

        logger.info(f"Loaded {len(known_encodings)} known encodings from {len(students)} students")
        return known_encodings, known_ids

    except Exception as e:
        logger.error(f"Error loading known faces: {e}", exc_info=True)
        return [], []


def recognize_from_frame(frame, known_encodings, known_ids):
    """
    Detect and recognize faces in a frame.
    Returns tuple of (recognized_student_ids set, annotated frame)
    """
    recognized_ids = set()
    
    try:
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame received")
            return recognized_ids, frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        
        if detector.empty():
            logger.error("Failed to load face cascade classifier")
            return recognized_ids, frame

        faces = detector.detectMultiScale(rgb, scaleFactor=1.2, minNeighbors=5)

        if len(faces) == 0:
            logger.debug("No faces detected in frame")
            return recognized_ids, frame

        logger.debug(f"Detected {len(faces)} face(s) in frame")

        for (x, y, w, h) in faces:
            face_img = rgb[y:y + h, x:x + w]

            try:
                objs = DeepFace.represent(
                    img_path=face_img,
                    model_name=MODEL_NAME,
                    enforce_detection=False
                )
            except Exception as e:
                logger.warning(f"DeepFace error on frame face: {e}")
                # Draw RED box for error
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, "Error", (x + 4, y + h - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                continue

            if not objs:
                # Draw RED box for no embedding
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, "No Face", (x + 4, y + h - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                continue

            emb = np.array(objs[0]["embedding"], dtype=np.float32)
            name = "Unknown"
            is_recognized = False

            if known_encodings:
                enc_mat = np.stack(known_encodings, axis=0)
                num = np.sum(enc_mat * emb, axis=1)
                den = (np.linalg.norm(enc_mat, axis=1) * np.linalg.norm(emb) + 1e-8)
                cos_sim = num / den
                cos_dist = 1.0 - cos_sim

                best_idx = int(np.argmin(cos_dist))
                best_dist = float(cos_dist[best_idx])

                if best_dist < DIST_THRESHOLD:
                    sid = known_ids[best_idx]
                    recognized_ids.add(sid)
                    is_recognized = True
                    try:
                        student = Student.objects.get(id=sid)
                        name = student.name
                        logger.debug(f"Recognized {name} (distance: {best_dist:.4f})")
                    except Student.DoesNotExist:
                        logger.warning(f"Student ID {sid} not found in database")

            # Draw box: GREEN if recognized, RED if unknown
            if is_recognized:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x + 4, y + h - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, "Unknown", (x + 4, y + h - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return recognized_ids, frame

    except Exception as e:
        logger.error(f"Error in recognize_from_frame: {e}", exc_info=True)
        return recognized_ids, frame
