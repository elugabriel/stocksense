from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Administrator"
        ORG_ADMIN = "org_admin", "Organization Administrator"
        BRANCH_MANAGER = "branch_manager", "Branch Manager"
        WAREHOUSE_MANAGER = "warehouse_manager", "Warehouse Manager"
        INVENTORY_OFFICER = "inventory_officer", "Inventory Officer"
        PROCUREMENT_OFFICER = "procurement_officer", "Procurement Officer"
        SALES_STAFF = "sales_staff", "Sales Staff (Cashier)"
        ACCOUNTANT = "accountant", "Accountant"
        VENDOR = "vendor", "Vendor (Portal)"
        EXECUTIVE = "executive", "Executive (Read-only Dashboard)"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.SALES_STAFF,
    )

    # Scope fields — these implement the "Scope" column from your role table.
    # Nullable because scope differs by role (e.g. Super Admin has none, Branch Manager has branch only).
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )
    warehouse = models.ForeignKey(
        "core.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"