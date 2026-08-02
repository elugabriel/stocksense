from django.db import models
from simple_history.models import HistoricalRecords
from datetime import timedelta
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    class WarehouseType(models.TextChoices):
        MAIN = "main", "Main Warehouse"
        BRANCH = "branch", "Branch Storage"
        TRANSIT = "transit", "Transit/Staging"
        COLD_STORAGE = "cold_storage", "Cold Storage"

    name = models.CharField(max_length=255)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warehouses",
    )
    warehouse_type = models.CharField(
        max_length=20,
        choices=WarehouseType.choices,
        default=WarehouseType.MAIN,
    )
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    capacity_units = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum stock capacity, in your chosen unit (e.g. pallets, cubic meters)",
    )
    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouses",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Product(models.Model):
    class UnitOfMeasure(models.TextChoices):
        PIECE = "piece", "Piece"
        KG = "kg", "Kilogram"
        LITER = "liter", "Liter"
        BOX = "box", "Box"
        PACK = "pack", "Pack"
        CARTON = "carton", "Carton"

    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.PIECE,
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    reorder_level = models.PositiveIntegerField(default=0)
    barcode = models.CharField(max_length=64, blank=True, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["barcode"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class BatchQuerySet(models.QuerySet):
    def expired(self):
        return self.filter(expiry_date__lt=timezone.now().date(), is_active=True)

    def expiring_soon(self, days=30):
        today = timezone.now().date()
        return self.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=days),
            is_active=True,
        )


class Batch(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    lot_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


    history = HistoricalRecords()
    objects = BatchQuerySet.as_manager()

    class Meta:
        unique_together = ("product", "lot_number", "warehouse")
        indexes = [
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["product", "warehouse"]),
        ]

    def __str__(self):
        return f"{self.product.sku} - Lot {self.lot_number}"


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_TRANSIT = "in_transit", "In Transit"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="transfers",
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers",
    )
    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="transfers_out",
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="transfers_in",
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    initiated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfers_initiated",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_approved",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source_warehouse", "destination_warehouse"]),
        ]

    def __str__(self):
        return f"{self.product.sku}: {self.source_warehouse} → {self.destination_warehouse}"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIVED = "received", "Stock Received"
        SALE = "sale", "Sale"
        TRANSFER_OUT = "transfer_out", "Transfer Out"
        TRANSFER_IN = "transfer_in", "Transfer In"
        ADJUSTMENT = "adjustment", "Manual Adjustment"
        RETURN = "return", "Customer Return"
        DAMAGE = "damage", "Damaged/Expired Removal"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField(
        help_text="Positive for stock increases, negative for decreases",
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Related transfer/sale/adjustment ID, if applicable",
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["product", "warehouse"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.product.sku} | {self.movement_type} | {self.quantity} @ {self.timestamp}"


class StockAdjustment(models.Model):
    class ReasonCode(models.TextChoices):
        DAMAGE = "damage", "Damaged Goods"
        EXPIRY = "expiry", "Expired Goods"
        THEFT = "theft", "Theft/Loss"
        COUNT_CORRECTION = "count_correction", "Physical Count Correction"
        SYSTEM_ERROR = "system_error", "System Error Correction"
        OTHER = "other", "Other"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adjustments",
    )
    quantity_change = models.IntegerField(
        help_text="Positive to increase stock, negative to decrease",
    )
    reason_code = models.CharField(max_length=30, choices=ReasonCode.choices)
    reason_notes = models.TextField(
        help_text="Mandatory explanation — required for every adjustment",
    )
    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="adjustments_requested",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adjustments_approved",
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.sku} | {self.reason_code} | {self.quantity_change}"
    
class DashboardPreference(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="dashboard_preference")
    selected_kpis = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s dashboard preferences"