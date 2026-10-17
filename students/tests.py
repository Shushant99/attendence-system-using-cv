import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from students.encoding_utils import create_encodings_for_student
from students.models import ClassRoom, Student


class CreateEncodingsForStudentTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media_root.cleanup)

        classroom = ClassRoom.objects.create(name='Test classroom')
        self.student = Student.objects.create(
            roll_no='T001',
            name='Test student',
            classroom=classroom,
        )
        self.student.photo.save('student.jpg', ContentFile(b'test photo'), save=True)
        self.photo_path = Path(self.student.photo.path)

    @patch('students.encoding_utils.build_embedding_for_student', return_value=True)
    def test_deletes_photo_after_embedding_is_generated(self, build_embedding):
        self.assertTrue(create_encodings_for_student(self.student))

        self.student.refresh_from_db()
        self.assertFalse(self.photo_path.exists())
        self.assertFalse(self.student.photo)
        build_embedding.assert_called_once_with(self.student)

    @patch('students.encoding_utils.build_embedding_for_student', return_value=False)
    def test_keeps_photo_when_embedding_generation_fails(self, build_embedding):
        self.assertFalse(create_encodings_for_student(self.student))

        self.student.refresh_from_db()
        self.assertTrue(self.photo_path.exists())
        self.assertTrue(self.student.photo)
        build_embedding.assert_called_once_with(self.student)
