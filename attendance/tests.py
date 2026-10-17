from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from attendance.models import AttendanceRecord, AttendanceSession
from students.models import ClassRoom, Student, Teacher


User = get_user_model()


class ManualAttendanceFrontendTests(TestCase):
    def setUp(self):
        self.classroom = ClassRoom.objects.create(name='Test classroom')
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='test-password',
            role='TEACHER',
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id='T001',
            department='Test',
        )
        self.teacher.assigned_classrooms.add(self.classroom)
        self.student = Student.objects.create(
            roll_no='S001',
            name='Test student',
            classroom=self.classroom,
        )
        self.session = AttendanceSession.objects.create(
            classroom=self.classroom,
            taken_by=self.teacher_user,
        )
        self.record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
        )
        self.client.force_login(self.teacher_user)

    def test_attendance_detail_renders_manual_status_controls(self):
        response = self.client.get(reverse(
            'attendance:attendance_detail',
            args=[self.session.pk],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'attendance-status-form')
        self.assertContains(response, 'value="LATE"')
        self.assertContains(response, 'value="LEAVE"')

    def test_manual_status_update_saves_and_tracks_teacher(self):
        response = self.client.post(
            reverse('attendance:update_record_status', args=[self.record.pk]),
            {'status': 'LATE'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'LATE')
        self.assertEqual(self.record.marked_by, self.teacher_user)

    def test_teacher_cannot_edit_unassigned_classroom_record(self):
        other_classroom = ClassRoom.objects.create(name='Other classroom')
        other_student = Student.objects.create(
            roll_no='S002',
            name='Other student',
            classroom=other_classroom,
        )
        other_record = AttendanceRecord.objects.create(
            session=AttendanceSession.objects.create(
                classroom=other_classroom,
                taken_by=self.teacher_user,
            ),
            student=other_student,
        )
        response = self.client.post(
            reverse('attendance:update_record_status', args=[other_record.pk]),
            {'status': 'PRESENT'},
        )

        self.assertEqual(response.status_code, 404)
        other_record.refresh_from_db()
        self.assertEqual(other_record.status, 'ABSENT')
