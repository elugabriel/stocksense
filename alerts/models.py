from django.db import models


class Alert(models.Model):
    class AlertType(models.TextChoices):
        REORDER = "reorder", "Reorder Level"
        CRITICAL = "critical", "Critical Threshold"
        EXPIRY = "expiry", "Expiry Approaching"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        OVERSTOCK = "overstock", "Overstock"
        ABNORMAL_MOVEMENT = "abnormal_movement", "Abnormal Movement"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    product = models.ForeignKey("core.Product", on_delete=models.CASCADE, related_name="alerts")
    warehouse = models.ForeignKey("core.Warehouse", on_delete=models.CASCADE, related_name="alerts", null=True, blank=True)
    batch = models.ForeignKey("core.Batch", on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity}] {self.alert_type}: {self.product.sku}"