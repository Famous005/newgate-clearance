from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    ROLE_CHOICES = [
        ('student',      'Student'),
        ('bursary',      'Bursary Officer'),
        ('unit_officer', 'Unit Officer'),
        ('admin',        'Administrator'),
    ]

    role            = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    matric_number   = models.CharField(max_length=20, blank=True, null=True, unique=True)
    department      = models.CharField(max_length=100, blank=True, null=True)
    phone           = models.CharField(max_length=15, blank=True, null=True)
    is_verified     = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    # ── Role helpers ──────────────────────────────────────────────────────────
    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_bursary(self):
        return self.role == 'bursary'

    @property
    def is_unit_officer(self):
        return self.role == 'unit_officer'

    @property
    def is_admin_user(self):
        return self.role == 'admin'