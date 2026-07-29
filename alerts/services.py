from django.db.models import Sum
from core.models import Product, Batch
from .models import Alert

from core.models import StockMovement
from django.db.models import Avg, StdDev
from django.utils import timezone
from datetime import timedelta


from django.core.mail import send_mail
from django.conf import settings

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def check_reorder_levels():
    """
    For every active product, sum stock across all active batches.
    If total is at or below reorder_level, create an alert (if one doesn't
    already exist and is unresolved for this product).
    """
    created_count = 0
    products = Product.objects.filter(is_active=True)

    for product in products:
        total_stock = (
            Batch.objects.filter(product=product, is_active=True)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        if total_stock <= product.reorder_level:
            already_alerted = Alert.objects.filter(
                product=product,
                alert_type=Alert.AlertType.REORDER,
                is_resolved=False,
            ).exists()

            if not already_alerted:
                Alert.objects.create(
                    alert_type=Alert.AlertType.REORDER,
                    severity=Alert.Severity.WARNING,
                    product=product,
                    message=f"{product.name} ({product.sku}) stock is at {total_stock}, at or below reorder level of {product.reorder_level}.",
                )
                created_count += 1

    return created_count


def check_out_of_stock():
    """
    For every active product with zero or negative total stock, create an alert.
    """
    created_count = 0
    products = Product.objects.filter(is_active=True)

    for product in products:
        total_stock = (
            Batch.objects.filter(product=product, is_active=True)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        if total_stock <= 0:
            already_alerted = Alert.objects.filter(
                product=product,
                alert_type=Alert.AlertType.OUT_OF_STOCK,
                is_resolved=False,
            ).exists()

            if not already_alerted:
                Alert.objects.create(
                    alert_type=Alert.AlertType.OUT_OF_STOCK,
                    severity=Alert.Severity.CRITICAL,
                    product=product,
                    message=f"{product.name} ({product.sku}) is out of stock.",
                )
                created_count += 1

    return created_count


def check_critical_threshold(critical_fraction=0.2):
    """
    Critical = stock has fallen to critical_fraction (default 20%) of the
    reorder level or below — a more urgent line than the reorder trigger itself.
    Skips products with reorder_level of 0 (nothing to measure against).
    """
    created_count = 0
    products = Product.objects.filter(is_active=True).exclude(reorder_level=0)

    for product in products:
        total_stock = (
            Batch.objects.filter(product=product, is_active=True)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )
        critical_level = product.reorder_level * critical_fraction

        if 0 < total_stock <= critical_level:
            already_alerted = Alert.objects.filter(
                product=product,
                alert_type=Alert.AlertType.CRITICAL,
                is_resolved=False,
            ).exists()

            if not already_alerted:
                Alert.objects.create(
                    alert_type=Alert.AlertType.CRITICAL,
                    severity=Alert.Severity.CRITICAL,
                    product=product,
                    message=f"{product.name} ({product.sku}) stock is critically low at {total_stock} (reorder level: {product.reorder_level}).",
                )
                created_count += 1

    return created_count


def check_expiry_alerts(warning_days=30):
    """
    Flags batches expiring within warning_days as EXPIRY alerts,
    and batches already past their expiry_date as a separate,
    more severe case using the same alert type but critical severity.
    """
    created_count = 0

    expiring_batches = Batch.objects.expiring_soon(days=warning_days)
    for batch in expiring_batches:
        already_alerted = Alert.objects.filter(
            batch=batch,
            alert_type=Alert.AlertType.EXPIRY,
            is_resolved=False,
        ).exists()

        if not already_alerted:
            Alert.objects.create(
                alert_type=Alert.AlertType.EXPIRY,
                severity=Alert.Severity.WARNING,
                product=batch.product,
                warehouse=batch.warehouse,
                batch=batch,
                message=f"{batch.product.name} (Lot {batch.lot_number}) expires on {batch.expiry_date} — within {warning_days} days.",
            )
            created_count += 1

    expired_batches = Batch.objects.expired()
    for batch in expired_batches:
        already_alerted = Alert.objects.filter(
            batch=batch,
            alert_type=Alert.AlertType.EXPIRY,
            severity=Alert.Severity.CRITICAL,
            is_resolved=False,
        ).exists()

        if not already_alerted:
            Alert.objects.create(
                alert_type=Alert.AlertType.EXPIRY,
                severity=Alert.Severity.CRITICAL,
                product=batch.product,
                warehouse=batch.warehouse,
                batch=batch,
                message=f"{batch.product.name} (Lot {batch.lot_number}) EXPIRED on {batch.expiry_date}.",
            )
            created_count += 1

    return created_count




def check_abnormal_movements(lookback_days=30, std_dev_multiplier=3):
    """
    Flags movements whose absolute quantity is more than std_dev_multiplier
    standard deviations above the average absolute movement size for that
    product over the lookback window. Requires at least 5 prior movements
    for a product before it can be evaluated (not enough data otherwise).
    """
    created_count = 0
    cutoff = timezone.now() - timedelta(days=lookback_days)

    recent_movements = StockMovement.objects.filter(timestamp__gte=cutoff)
    product_ids = recent_movements.values_list("product_id", flat=True).distinct()

    for product_id in product_ids:
        product_movements = recent_movements.filter(product_id=product_id)

        if product_movements.count() < 5:
            continue

        stats = product_movements.aggregate(
            avg_qty=Avg("quantity"),
            std_qty=StdDev("quantity"),
        )
        avg_qty = stats["avg_qty"] or 0
        std_qty = stats["std_qty"] or 0

        if std_qty == 0:
            continue

        threshold = abs(avg_qty) + (std_dev_multiplier * std_qty)

        for movement in product_movements:
            if abs(movement.quantity) > threshold:
                already_alerted = Alert.objects.filter(
                    product_id=product_id,
                    alert_type=Alert.AlertType.ABNORMAL_MOVEMENT,
                    is_resolved=False,
                    message__contains=f"movement #{movement.id}",
                ).exists()

                if not already_alerted:
                    Alert.objects.create(
                        alert_type=Alert.AlertType.ABNORMAL_MOVEMENT,
                        severity=Alert.Severity.WARNING,
                        product_id=product_id,
                        warehouse=movement.warehouse,
                        batch=movement.batch,
                        message=f"Unusual movement #{movement.id} for {movement.product.sku}: quantity {movement.quantity} is far outside the typical range (avg {avg_qty:.1f}, threshold ±{threshold:.1f}).",
                    )
                    created_count += 1

    return created_count



def send_alert_email(alert, recipient_email):
    subject = f"[StockSense Alert] {alert.get_severity_display()}: {alert.get_alert_type_display()}"
    body = (
        f"{alert.message}\n\n"
        f"Product: {alert.product.name} ({alert.product.sku})\n"
        f"Severity: {alert.get_severity_display()}\n"
        f"Created: {alert.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Log in to StockSense to review and resolve this alert."
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def notify_unsent_alerts(recipient_email):
    """
    Sends email for every unresolved alert that hasn't been emailed yet.
    Uses a simple approach: track via a new field rather than re-sending
    every unresolved alert every time this runs.
    """
    from .models import Alert
    unsent = Alert.objects.filter(is_resolved=False, email_sent=False)

    sent_count = 0
    for alert in unsent:
        send_alert_email(alert, recipient_email)
        alert.email_sent = True
        alert.save(update_fields=["email_sent"])
        sent_count += 1

    return sent_count




def send_alert_sms(alert, recipient_phone_number):
    """
    Sends an SMS for a single alert via Twilio. Does nothing (returns False)
    if SMS_ALERTS_ENABLED is off or credentials aren't configured — this
    makes it safe to call from anywhere without crashing in environments
    that haven't set up Twilio yet.
    """
    if not settings.SMS_ALERTS_ENABLED:
        return False

    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        return False

    body = f"[StockSense {alert.get_severity_display()}] {alert.message}"
    # SMS has a practical length limit — trim long messages
    if len(body) > 300:
        body = body[:297] + "..."

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=recipient_phone_number,
        )
        return True
    except TwilioRestException as e:
        # Log and continue rather than crashing the whole alert pipeline
        print(f"SMS send failed for alert {alert.id}: {e}")
        return False


def notify_unsent_sms_alerts(recipient_phone_number, severity_filter=None):
    """
    Sends SMS only for CRITICAL alerts by default (SMS is meant for urgent
    cases only, per the checklist item) — pass severity_filter to override.
    """
    from .models import Alert

    severities = severity_filter or [Alert.Severity.CRITICAL]
    unsent = Alert.objects.filter(
        is_resolved=False,
        sms_sent=False,
        severity__in=severities,
    )

    sent_count = 0
    for alert in unsent:
        if send_alert_sms(alert, recipient_phone_number):
            alert.sms_sent = True
            alert.save(update_fields=["sms_sent"])
            sent_count += 1

    return sent_count