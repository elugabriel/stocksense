"""Populate the database with a realistic UK demo dataset.

    python manage.py seed_demo            # create/update demo data
    python manage.py seed_demo --flush    # wipe existing demo data first

Everything is UK-based: sterling pricing, UK-registered supplier companies and
warehouses/branches in UK cities. Designed so the dashboards, profit-margin
report and the Product Performance comparison all have real numbers to show.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Batch,
    Branch,
    Category,
    Product,
    StockMovement,
    Warehouse,
)
from sales.models import Sale, SaleLine
from vendors.models import PurchaseOrder, PurchaseOrderLine, Vendor

User = get_user_model()

DEMO_PASSWORD = "demo1234"

# name, city, country, capacity for the main warehouse
BRANCHES = [
    ("NJSmartStock London", "London", "United Kingdom"),
    ("NJSmartStock Manchester", "Manchester", "United Kingdom"),
    ("NJSmartStock Birmingham", "Birmingham", "United Kingdom"),
    ("NJSmartStock Leeds", "Leeds", "United Kingdom"),
]

# role -> (username, branch index or None)
DEMO_USERS = [
    ("org_admin", "admin", None),
    ("executive", "exec", None),
    ("branch_manager", "bmanager", 0),
    ("warehouse_manager", "wmanager", 0),
    ("inventory_officer", "inventory", 1),
    ("procurement_officer", "procurement", None),
    ("sales_staff", "cashier", 0),
    ("accountant", "accounts", None),
]

CATEGORIES = [
    "Beverages",
    "Bakery",
    "Household",
    "Personal Care",
    "Snacks",
    "Frozen",
]

# name, city, country, payment terms, lead time days
VENDORS = [
    ("Britvic Soft Drinks Ltd", "Hemel Hempstead", "United Kingdom", "Net 30", 7),
    ("Warburtons Ltd", "Bolton", "United Kingdom", "Net 14", 3),
    ("Unilever UK Ltd", "Kingston upon Thames", "United Kingdom", "Net 45", 10),
    ("Nestle UK Ltd", "Gatwick", "United Kingdom", "Net 30", 9),
    ("Hovis Ltd", "High Wycombe", "United Kingdom", "Net 14", 4),
    ("Princes Ltd", "Liverpool", "United Kingdom", "50% deposit, balance on delivery", 12),
]

# name, category, cost price, selling price
PRODUCTS = [
    ("Still Water 500ml", "Beverages", "0.18", "0.55"),
    ("Sparkling Water 1L", "Beverages", "0.32", "0.95"),
    ("Cola 330ml Can", "Beverages", "0.24", "0.75"),
    ("Orange Juice 1L", "Beverages", "0.85", "1.80"),
    ("English Breakfast Tea 80s", "Beverages", "1.40", "2.99"),
    ("Instant Coffee 200g", "Beverages", "2.60", "4.75"),
    ("White Sliced Bread 800g", "Bakery", "0.55", "1.15"),
    ("Wholemeal Loaf 800g", "Bakery", "0.60", "1.25"),
    ("6 Bread Rolls", "Bakery", "0.48", "1.10"),
    ("All Butter Croissants x4", "Bakery", "1.10", "2.25"),
    ("Washing Up Liquid 500ml", "Household", "0.70", "1.50"),
    ("Kitchen Roll x2", "Household", "1.20", "2.40"),
    ("Bin Bags 30pk", "Household", "1.05", "2.10"),
    ("Laundry Detergent 1.9L", "Household", "3.20", "6.00"),
    ("Toilet Tissue 9 Roll", "Household", "2.80", "5.25"),
    ("Shampoo 400ml", "Personal Care", "1.35", "2.80"),
    ("Shower Gel 500ml", "Personal Care", "1.10", "2.30"),
    ("Toothpaste 100ml", "Personal Care", "0.75", "1.85"),
    ("Hand Soap 250ml", "Personal Care", "0.65", "1.45"),
    ("Salted Crisps 6pk", "Snacks", "0.90", "1.90"),
    ("Milk Chocolate Bar 100g", "Snacks", "0.60", "1.30"),
    ("Mixed Nuts 200g", "Snacks", "1.25", "2.60"),
    ("Digestive Biscuits 400g", "Snacks", "0.55", "1.20"),
    ("Garden Peas 900g", "Frozen", "1.00", "1.95"),
    ("Fish Fingers 12pk", "Frozen", "1.40", "2.85"),
    ("Vanilla Ice Cream 2L", "Frozen", "1.80", "3.50"),
]

PAYMENT_METHODS = ["cash", "card", "card", "card", "bank_transfer", "mobile_money"]


class Command(BaseCommand):
    help = "Populate the database with a UK-based demo dataset (sterling pricing)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="How many days of sales history to generate (default: 60).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)

        if options["flush"]:
            self._flush()

        categories = self._seed_categories()
        branches, warehouses = self._seed_locations()
        self._seed_users(branches, warehouses)
        vendors = self._seed_vendors()
        products = self._seed_products(categories)
        self._seed_batches(products, warehouses, rng)
        self._seed_sales(products, warehouses, options["days"], rng)
        self._seed_purchase_orders(vendors, products, rng)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {len(branches)} branches, {len(warehouses)} warehouses, "
            f"{len(vendors)} vendors, {len(products)} products. "
            f"Log in with any of: {', '.join(u[1] for u in DEMO_USERS)} / {DEMO_PASSWORD}"
        ))

    # ------------------------------------------------------------------ flush
    def _flush(self):
        self.stdout.write("Flushing existing demo data...")
        StockMovement.objects.all().delete()
        SaleLine.objects.all().delete()
        Sale.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        Batch.objects.all().delete()
        Product.objects.all().delete()
        Vendor.objects.all().delete()
        Warehouse.objects.all().delete()
        Branch.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    # ------------------------------------------------------------- categories
    def _seed_categories(self):
        categories = {}
        for name in CATEGORIES:
            categories[name], _ = Category.objects.get_or_create(name=name)
        return categories

    # -------------------------------------------------------------- locations
    def _seed_locations(self):
        branches = []
        warehouses = []
        for name, city, country in BRANCHES:
            branch, _ = Branch.objects.get_or_create(
                name=name,
                defaults={"city": city, "country": country, "address": f"1 High Street, {city}"},
            )
            branch.city, branch.country = city, country
            branch.save()
            branches.append(branch)

            main, _ = Warehouse.objects.get_or_create(
                name=f"{city} Main Warehouse",
                defaults={
                    "branch": branch,
                    "warehouse_type": Warehouse.WarehouseType.MAIN,
                    "city": city,
                    "country": country,
                    "capacity_units": 5000,
                },
            )
            store, _ = Warehouse.objects.get_or_create(
                name=f"{city} Shop Floor",
                defaults={
                    "branch": branch,
                    "warehouse_type": Warehouse.WarehouseType.BRANCH,
                    "city": city,
                    "country": country,
                    "capacity_units": 800,
                },
            )
            for wh in (main, store):
                wh.branch = branch
                wh.city, wh.country = city, country
                wh.save()
            warehouses.extend([main, store])
        return branches, warehouses

    # ------------------------------------------------------------------ users
    def _seed_users(self, branches, warehouses):
        for role, username, branch_idx in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@njsmartstock.local", "role": role},
            )
            user.role = role
            user.email = f"{username}@njsmartstock.local"
            if branch_idx is not None:
                user.branch = branches[branch_idx]
                user.warehouse = warehouses[branch_idx * 2]
            user.set_password(DEMO_PASSWORD)
            user.save()

    # ---------------------------------------------------------------- vendors
    def _seed_vendors(self):
        vendors = []
        for name, city, country, terms, lead in VENDORS:
            vendor, _ = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    "city": city,
                    "country": country,
                    "payment_terms": terms,
                    "default_lead_time_days": lead,
                    "contact_person": "Accounts Team",
                    "email": f"orders@{name.split()[0].lower()}.example",
                    "phone": "+44 20 7946 0000",
                    "address": f"Unit 4, {city} Trade Park",
                },
            )
            vendors.append(vendor)
        return vendors

    # --------------------------------------------------------------- products
    def _seed_products(self, categories):
        products = []
        for idx, (name, cat, cost, sell) in enumerate(PRODUCTS, start=1):
            sku = f"NJS-{idx:04d}"
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories[cat],
                    "cost_price": Decimal(cost),
                    "selling_price": Decimal(sell),
                    "reorder_level": 40,
                    "barcode": f"50{idx:011d}",
                },
            )
            product.name = name
            product.category = categories[cat]
            product.cost_price = Decimal(cost)
            product.selling_price = Decimal(sell)
            product.save()
            products.append(product)
        return products

    # ---------------------------------------------------------------- batches
    def _seed_batches(self, products, warehouses, rng):
        today = timezone.now().date()
        for product in products:
            for wh in warehouses:
                if rng.random() < 0.15:
                    continue  # not every product is in every warehouse
                qty = rng.choice([0, 25, 60, 120, 180, 240, 300])
                expiry = today + timedelta(days=rng.choice([20, 45, 90, 180, 365]))
                Batch.objects.get_or_create(
                    product=product,
                    warehouse=wh,
                    lot_number=f"LOT-{product.sku[-4:]}-{wh.id}",
                    defaults={
                        "quantity": qty,
                        "unit_cost": product.cost_price,
                        "expiry_date": expiry,
                    },
                )

    # ------------------------------------------------------------------ sales
    def _seed_sales(self, products, warehouses, days, rng):
        if Sale.objects.exists():
            self.stdout.write("Sales already present - skipping sales generation.")
            return

        cashier = User.objects.filter(role="sales_staff").first()
        shop_floors = [w for w in warehouses if w.warehouse_type == Warehouse.WarehouseType.BRANCH]
        now = timezone.now()
        seq = 0

        for day_offset in range(days, 0, -1):
            day = now - timedelta(days=day_offset)
            # weekends busier
            base = 6 if day.weekday() >= 5 else 4
            for _ in range(rng.randint(base, base + 6)):
                seq += 1
                warehouse = rng.choice(shop_floors)
                ts = day.replace(
                    hour=rng.randint(8, 20),
                    minute=rng.randint(0, 59),
                    second=rng.randint(0, 59),
                    microsecond=0,
                )
                sale = Sale.objects.create(
                    sale_number=f"SALE-{ts:%Y%m%d}-{seq:04d}",
                    branch=warehouse.branch,
                    warehouse=warehouse,
                    customer_name=rng.choice(
                        ["Walk-in customer", "A. Patel", "J. Smith", "R. Okafor", "L. Nguyen", "M. O'Brien"]
                    ),
                    payment_method=rng.choice(PAYMENT_METHODS),
                    sold_by=cashier,
                )
                subtotal = Decimal("0.00")
                for product in rng.sample(products, rng.randint(1, 5)):
                    qty = rng.randint(1, 6)
                    unit_price = product.selling_price
                    line_total = unit_price * qty
                    subtotal += line_total
                    SaleLine.objects.create(
                        sale=sale,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        line_total=line_total,
                    )
                    mv = StockMovement.objects.create(
                        product=product,
                        warehouse=warehouse,
                        movement_type=StockMovement.MovementType.SALE,
                        quantity=-qty,
                        reference_id=str(sale.id),
                        performed_by=cashier,
                        notes=f"Sale {sale.sale_number}",
                    )
                    StockMovement.objects.filter(pk=mv.pk).update(timestamp=ts)

                discount = Decimal("0.00")
                if rng.random() < 0.1:
                    discount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
                sale.subtotal = subtotal
                sale.discount = discount
                sale.total = subtotal - discount
                sale.save()
                Sale.objects.filter(pk=sale.pk).update(created_at=ts)

    # -------------------------------------------------------- purchase orders
    def _seed_purchase_orders(self, vendors, products, rng):
        if PurchaseOrder.objects.exists():
            self.stdout.write("Purchase orders already present - skipping PO generation.")
            return

        creator = User.objects.filter(role="procurement_officer").first()
        statuses = [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.SENT,
            PurchaseOrder.Status.CONFIRMED,
            PurchaseOrder.Status.RECEIVED,
        ]
        seq = 0
        for vendor in vendors:
            for _ in range(rng.randint(1, 3)):
                seq += 1
                status = rng.choice(statuses)
                po = PurchaseOrder.objects.create(
                    vendor=vendor,
                    order_number=f"PO-{seq:04d}",
                    status=status,
                    created_by=creator,
                    expected_delivery_date=timezone.now().date() + timedelta(days=vendor.default_lead_time_days or 7),
                )
                for product in rng.sample(products, rng.randint(2, 5)):
                    ordered = rng.choice([50, 100, 150, 200])
                    received = ordered if status == PurchaseOrder.Status.RECEIVED else 0
                    PurchaseOrderLine.objects.create(
                        purchase_order=po,
                        product=product,
                        quantity_ordered=ordered,
                        quantity_received=received,
                        unit_cost=product.cost_price,
                    )
