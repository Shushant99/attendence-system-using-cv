from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PARENT')

    def is_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    def is_teacher(self):
        return self.role == 'TEACHER'

    def is_parent(self):
        return self.role == 'PARENT'

    def get_role_display_verbose(self):
        """Return verbose role name."""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
