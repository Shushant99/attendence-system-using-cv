# students/encoding_utils.py

from attendance.face_utils import build_embedding_for_student


def create_encodings_for_student(student):
    """
    Build DeepFace embeddings for a student's main photo.
    Called after saving a student with a photo.
    """
    build_embedding_for_student(student)
