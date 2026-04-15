from django.core.mail import send_mail
from django.conf import settings
import uuid

from .tasks import send_email_task


def generate_token():
    """Generate a unique token for email activation or password reset."""
    return str(uuid.uuid4())


def send_activation_email(user, request):
    """Send account activation email to the user."""
    token = generate_token()
    user.activation_token = token
    user.save()

    activation_link = f"{settings.SITE_DOMAIN}/users/activate/{user.id}/{token}/"

    subject = f"Activate Your {settings.SITE_NAME} Account"
    message = f"""
Hi {user.username},

Thank you for registering with {settings.SITE_NAME}.

Please click the link below to activate your account:
{activation_link}

This link will work to activate your account.

If you did not register, please ignore this email.

Best regards,
{settings.SITE_NAME} Team
    """

    try:
        send_email_task.delay(subject, message, user.email)
        return True
    except Exception as e:
        # Fallback to sync send if broker is temporarily unavailable.
        print(f"Email queue failed, falling back to sync send: {e}")
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as sync_error:
            print(f"Email sending failed: {sync_error}")
            return False


def send_password_reset_email(user, request):
    """Send password reset email to the user."""
    token = generate_token()
    user.activation_token = token  # Reusing token field for reset too
    user.save()

    reset_link = f"{settings.SITE_DOMAIN}/users/reset-password/{user.id}/{token}/"

    subject = f"Reset Your {settings.SITE_NAME} Password"
    message = f"""
Hi {user.username},

You requested a password reset for your {settings.SITE_NAME} account.

Please click the link below to set a new password:
{reset_link}

If you did not request this, please ignore this email.

Best regards,
{settings.SITE_NAME} Team
    """

    try:
        send_email_task.delay(subject, message, user.email)
        return True
    except Exception as e:
        # Fallback to sync send if broker is temporarily unavailable.
        print(f"Password reset queue failed, falling back to sync send: {e}")
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception as sync_error:
            print(f"Password reset email failed: {sync_error}")
            return False