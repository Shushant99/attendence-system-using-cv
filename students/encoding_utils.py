# students/encoding_utils.py

from attendance.face_utils import build_embedding_for_student


def create_encodings_for_student(student):
    """
    Build DeepFace embeddings for a student's main photo.
    Delete the source photo only after the embedding has been saved successfully.
    """
    if not build_embedding_for_student(student):
        return False

    student.photo.delete(save=True)
    return True
