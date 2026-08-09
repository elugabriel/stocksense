from celery import shared_task
from core.services import generate_performance_summary
from alerts.services import send_alert_email


@shared_task
def generate_and_send_weekly_summary(recipient_email=None):
    summary = generate_performance_summary(period_days=7)

    if recipient_email:
        from django.core.mail import send_mail
        from django.conf import settings

        send_mail(
            subject=f"StockSense Weekly Summary — {summary['generated_at'][:10]}",
            message=summary["summary_text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

    return summary["summary_text"]