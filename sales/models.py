from django.db import models
from simple_history.models import HistoricalRecords


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        OTHER = "other", "Other"

    sale_number = models.CharField(max_length=100, unique=True)
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales")
    warehouse = models.ForeignKey("core.Warehouse", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales")

    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    sold_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="sales_made")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.sale_number} — {self.total}"


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("core.Product", on_delete=models.CASCADE, related_name="sale_lines")
    batch = models.ForeignKey("core.Batch", on_delete=models.SET_NULL, null=True, blank=True, related_name="sale_lines")

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.sku} x{self.quantity}"