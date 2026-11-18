from django.db import models
from django.conf import settings

class AcademicSession(models.Model):
    name       = models.CharField(max_length=20, unique=True)  # e.g. 2024/2025
    is_active  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only one session can be active at a time
        if self.is_active:
            AcademicSession.objects.exclude(pk=self.pk).update(
                is_active=False
            )
        super().save(*args, **kwargs)

class Unit(models.Model):
    """Represents a clearance unit e.g. Library, Medical, HOD etc."""

    name        = models.CharField(max_length=100)
    order       = models.PositiveIntegerField(unique=True)  # defines the approval sequence
    officer     = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='assigned_unit',
                    limit_choices_to={'role': 'unit_officer'}
                  )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.order}. {self.name}'


class ClearanceRequest(models.Model):
    """One clearance request per student per session."""

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('cleared',  'Cleared'),
        ('declined', 'Declined'),
    ]

    student             = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='clearance_requests',
                            limit_choices_to={'role': 'student'}
                          )
    session_year        = models.CharField(max_length=20)   # e.g. 2024/2025
    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    bursary_confirmed   = models.BooleanField(default=False)
    bursary_confirmed_by = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='bursary_confirmations',
                            limit_choices_to={'role': 'bursary'}
                          )
    bursary_confirmed_at = models.DateTimeField(null=True, blank=True)
    current_unit        = models.ForeignKey(
                            Unit,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='current_requests'
                          )
    submitted_at        = models.DateTimeField(auto_now_add=True)
    completed_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        # one request per student per session
        unique_together = ('student', 'session_year')
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.student} — {self.session_year} [{self.status}]'


class Approval(models.Model):
    """One approval record per unit per clearance request."""

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    request     = models.ForeignKey(
                    ClearanceRequest,
                    on_delete=models.CASCADE,
                    related_name='approvals'
                  )

    unit        = models.ForeignKey(
                    Unit,
                    on_delete=models.CASCADE,
                    related_name='approvals'
                  )
    officer     = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='approval_actions'
                  )
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    remarks     = models.TextField(blank=True, null=True)
    actioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # one approval record per unit per request
        unique_together = ('request', 'unit')
        ordering = ['unit__order']

    def __str__(self):
        return f'{self.unit} — {self.request.student} [{self.status}]'

class Notification(models.Model):
    user       = models.ForeignKey(
                   settings.AUTH_USER_MODEL,
                   on_delete=models.CASCADE,
                   related_name='notifications'
                 )
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.title}'