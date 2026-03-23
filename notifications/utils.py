import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Notification


User = get_user_model()
logger = logging.getLogger(__name__)


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


def _normalize_phone_number(raw_phone):
    if not raw_phone:
        return ''

    normalized = ''.join(ch for ch in str(raw_phone).strip() if ch.isdigit() or ch == '+')
    if not normalized:
        return ''

    if normalized.startswith('+'):
        return normalized

    default_cc = getattr(settings, 'WHATSAPP_DEFAULT_COUNTRY_CODE', '+977')
    if normalized.startswith('0'):
        normalized = normalized[1:]
    return f'{default_cc}{normalized}'


def send_whatsapp_message(phone_number, message_text):
    """Send a WhatsApp message via Twilio. Returns True when request is accepted."""
    if not getattr(settings, 'WHATSAPP_NOTIFICATIONS_ENABLED', False):
        return False

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')
    if not account_sid or not auth_token or not from_number:
        logger.warning('WhatsApp is enabled but Twilio configuration is incomplete.')
        return False

    normalized_phone = _normalize_phone_number(phone_number)
    if not normalized_phone:
        return False

    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message_text,
            from_=from_number if from_number.startswith('whatsapp:') else f'whatsapp:{from_number}',
            to=f'whatsapp:{normalized_phone}',
        )
        return True
    except Exception as exc:
        logger.warning('Failed to send WhatsApp message to %s: %s', normalized_phone, exc)
        return False


def notify_patient_whatsapp(patient_profile, message_text):
    """Send WhatsApp to a patient profile if phone number is available."""
    if not patient_profile:
        return False
    return send_whatsapp_message(getattr(patient_profile, 'phone', ''), message_text)
