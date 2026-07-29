from django.db import models
from simple_history.models import HistoricalRecords


class Vendor(models.Model):
    class VendorStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    performance_score_updated_at = models.DateTimeField(null=True, blank=True)

    payment_terms = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'Net 30', '50% deposit, balance on delivery'",
    )
    default_lead_time_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Vendor's typically quoted lead time, in days",
    )

    status = models.CharField(max_length=20, choices=VendorStatus.choices, default=VendorStatus.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent to Vendor"
        CONFIRMED = "confirmed", "Confirmed"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Fully Received"
        CANCELLED = "cancelled", "Cancelled"

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="purchase_orders")
    order_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)

    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="purchase_orders_created")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.order_number} — {self.vendor.name}"


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("core.Product", on_delete=models.CASCADE, related_name="purchase_order_lines")
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.sku} x{self.quantity_ordered}"