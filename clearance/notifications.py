from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


def notify(user, title, message, send_email=True):
    """
    Create an in-app notification and optionally send an email.
    """
    # ── In-app notification ───────────────────────────────────────────────────
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
    )

    # ── Email notification ────────────────────────────────────────────────────
    if send_email and user.email:
        try:
            send_mail(
                subject=f'[NUM Clearance] {title}',
                message=f'Dear {user.get_full_name()},\n\n{message}\n\n'
                        f'Log in to track your clearance progress:\n'
                        f'http://127.0.0.1:8080/\n\n'
                        f'Newgate University Minna\n'
                        f'Explore to Excel',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,  # never crash the app over email
            )
        except Exception:
            pass  # email failure must never block the workflow


def notify_bursary_confirmed(clearance_request):
    notify(
        user=clearance_request.student,
        title='Payment Confirmed — Clearance Started',
        message=(
            f'Your clearance fee payment has been confirmed by the Bursary. '
            f'Your clearance request for {clearance_request.session_year} '
            f'has been activated and routed to the Library unit for approval.'
        )
    )


def notify_unit_approved(clearance_request, unit_name, next_unit_name=None):
    if next_unit_name:
        message = (
            f'Your clearance has been approved by the {unit_name}. '
            f'It has been forwarded to the {next_unit_name} for the next approval.'
        )
    else:
        message = (
            f'Your clearance has been approved by the {unit_name}.'
        )
    notify(
        user=clearance_request.student,
        title=f'{unit_name} — Approved',
        message=message
    )


def notify_unit_declined(clearance_request, unit_name, remarks):
    notify(
        user=clearance_request.student,
        title=f'{unit_name} — Clearance Declined',
        message=(
            f'Your clearance request has been declined by the {unit_name}.\n\n'
            f'Reason: {remarks}\n\n'
            f'Please contact the {unit_name} to resolve this issue, '
            f'then ask the administrator to reactivate your request.'
        )
    )


def notify_cleared(clearance_request):
    notify(
        user=clearance_request.student,
        title='Clearance Complete — You Are Fully Cleared!',
        message=(
            f'Congratulations! Your final-year clearance for '
            f'{clearance_request.session_year} is now complete. '
            f'All units have approved your request. '
            f'You may now log in and download your clearance certificate.'
        )
    )


def notify_officer(officer, student_name, unit_name):
    """Notify a unit officer that a new request is in their queue."""
    notify(
        user=officer,
        title=f'New Clearance Request — {unit_name}',
        message=(
            f'{student_name} has a clearance request pending your approval '
            f'at the {unit_name}. Please log in to review and action it.'
        )
    )