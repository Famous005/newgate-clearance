from django import template
from clearance.models import Notification

register = template.Library()


@register.simple_tag
def unread_count(user):
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()