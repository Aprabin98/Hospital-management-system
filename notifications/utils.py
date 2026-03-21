from django.contrib.auth import get_user_model

from .models import Notification


User = get_user_model()


def create_notification(recipient, title, message, notification_type='GENERAL', action_url='', metadata=None):
    if recipient is None:
        return None

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        action_url=action_url,
        metadata=metadata or {},
    )


def notify_role(role, title, message, notification_type='GENERAL', action_url='', metadata=None):
    users = User.objects.filter(role=role, is_active=True)
    notifications = []
    for user in users:
        notifications.append(
            create_notification(
                recipient=user,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url,
                metadata=metadata,
            )
        )
    return notifications


def notify_roles(roles, title, message, notification_type='GENERAL', action_url='', metadata=None):
    created = []
    for role in roles:
        created.extend(notify_role(role, title, message, notification_type, action_url, metadata))
    return created
