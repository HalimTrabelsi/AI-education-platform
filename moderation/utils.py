from django.core.mail import send_mail
from django.conf import settings

def notify_user(user_email, subject, message):
    if not user_email:
        return False
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print("Email sending error:", e)
        return False
