from django.db import models
from django.conf import settings


class ClassRoom(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Student(models.Model):
    roll_no = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students')
    photo = models.ImageField(upload_to='student_photos/')

    class Meta:
        ordering = ['roll_no']
        indexes = [
            models.Index(fields=['classroom', 'roll_no']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f'{self.roll_no} - {self.name}'


class StudentImage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='student_photos/extra/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Image of {self.student.name}'


class Teacher(models.Model):
    """Teacher/Staff model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.department}"