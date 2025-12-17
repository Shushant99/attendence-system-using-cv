# attendance/face_utils.py

import os
from pathlib import Path
import numpy as np
import cv2
import traceback

from django.conf import settings
from deepface import DeepFace
from students.models import Student


ENC_DIR = Path(settings.MEDIA_ROOT) / "encodings_deepface"
MODEL_NAME = "Facenet"
DIST_THRESHOLD = 0.65


def _ensure_dir():
    ENC_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG] Encoding directory: {ENC_DIR}")
    print(f"[DEBUG] Directory exists: {ENC_DIR.exists()}")
    print(f"[DEBUG] Is writable: {os.access(ENC_DIR, os.W_OK)}")


def build_embedding_for_student(student):
    """
    Build embedding for a student. Print debug info.
    """
    if not student.photo:
        print(f"[ERROR] Student {student.id} has no photo")
        return

    _ensure_dir()
    
    # Convert to absolute string path (Windows compatibility)
    img_path = str(student.photo.path)
    print(f"[DEBUG] Building embedding for student {student.id}: {img_path}")
    print(f"[DEBUG] File exists: {os.path.exists(img_path)}")

    try:
        # DeepFace.represent returns list of dicts
        objs = DeepFace.represent(
            img_path=img_path,
            model_name=MODEL_NAME,
            enforce_detection=False
        )
        
        if not objs:
            print(f"[ERROR] No embedding generated for student {student.id}")
            return
        
        embedding = np.array(objs[0]["embedding"], dtype=np.float32)
        print(f"[DEBUG] Embedding shape: {embedding.shape}")

        enc_file = ENC_DIR / f"student_{student.id}_{MODEL_NAME}.npy"
        np.save(str(enc_file), embedding)
        print(f"[SUCCESS] Saved encoding to: {enc_file}")

    except Exception as e:
        print(f"[ERROR] Exception for student {student.id}: {str(e)}")
        traceback.print_exc()


def load_known_faces():
    """
    Load all stored embeddings.
    """
    _ensure_dir()
    known_encodings = []
    known_ids = []

    for student in Student.objects.all():
        enc_file = ENC_DIR / f"student_{student.id}_{MODEL_NAME}.npy"
        if enc_file.exists():
            emb = np.load(str(enc_file))
            known_encodings.append(emb)
            known_ids.append(student.id)
            print(f"[DEBUG] Loaded encoding for student {student.id}")

    print(f"[INFO] Loaded {len(known_encodings)} known encodings")
    return known_encodings, known_ids


def recognize_from_frame(frame, known_encodings, known_ids):
    """
    Detect faces, recognize, annotate with GREEN for recognized and RED for unknown.
    """
    recognized_ids = set()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    faces = detector.detectMultiScale(rgb, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in faces:
        face_img = rgb[y:y + h, x:x + w]

        try:
            objs = DeepFace.represent(
                img_path=face_img,
                model_name=MODEL_NAME,
                enforce_detection=False
            )
        except Exception as e:
            print(f"[WARN] DeepFace error on frame face: {str(e)}")
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

            print(f"[MATCH] Best distance: {best_dist:.4f}, Threshold: {DIST_THRESHOLD}")

            if best_dist < DIST_THRESHOLD:
                sid = known_ids[best_idx]
                recognized_ids.add(sid)
                is_recognized = True
                student = Student.objects.get(id=sid)
                name = student.name
                print(f"[RECOGNIZED] {name} (distance: {best_dist:.4f})")

        # Draw box: GREEN if recognized, RED if unknown
        if is_recognized:
            # GREEN box + black text
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (x + 4, y + h - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        else:
            # RED box + white text for "Unknown"
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y + h - 22), (x + w, y + h), (0, 0, 255), cv2.FILLED)
            cv2.putText(frame, "Unknown", (x + 4, y + h - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return recognized_ids, frame