from django.db import models
from django.conf import settings
from students.models import Student, ClassRoom


class AttendanceSession(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField(auto_now_add=True, db_index=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='attendance_sessions')

    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['classroom', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['taken_by']),
        ]
        unique_together = ('classroom', 'date')

    def __str__(self):
        return f'{self.classroom} - {self.date}'


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('LEAVE', 'Leave'),
    )
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABSENT')
    timestamp = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['student']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['student', 'session']),
        ]

    def __str__(self):
        return f'{self.student} - {self.session} - {self.status}'
