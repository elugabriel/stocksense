from .models import Batch, Product
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from sales.models import SaleLine, Sale
from alerts.models import Alert
from vendors.models import Vendor
from .models import Batch, Product, Warehouse
from .models import Batch, Product, Warehouse, StockMovement, Branch



def compare_branch_performance():
    branches = Branch.objects.filter(is_active=True)
    comparison = []

    for branch in branches:
        warehouses = Warehouse.objects.filter(branch=branch, is_active=True)
        batches = Batch.objects.filter(warehouse__in=warehouses, is_active=True, quantity__gt=0)

        total_stock_units = sum(b.quantity for b in batches)
        stock_value = sum(b.quantity * (b.unit_cost or b.product.cost_price) for b in batches)

        sales_30d = Sale.objects.filter(
            branch=branch,
            created_at__gte=timezone.now() - timedelta(days=30),
        )
        revenue_30d = sales_30d.aggregate(total=Sum("total"))["total"] or 0

        comparison.append({
            "branch_id": branch.id,
            "branch_name": branch.name,
            "city": branch.city,
            "warehouse_count": warehouses.count(),
            "total_stock_units": total_stock_units,
            "stock_value": str(round(stock_value, 2)),
            "revenue_last_30_days": str(revenue_30d),
        })

    # Warehouses with no branch assigned — group these under "Unassigned"
    unassigned_warehouses = Warehouse.objects.filter(branch__isnull=True, is_active=True)
    if unassigned_warehouses.exists():
        batches = Batch.objects.filter(warehouse__in=unassigned_warehouses, is_active=True, quantity__gt=0)
        total_stock_units = sum(b.quantity for b in batches)
        stock_value = sum(b.quantity * (b.unit_cost or b.product.cost_price) for b in batches)

        comparison.append({
            "branch_id": None,
            "branch_name": "Unassigned Warehouses",
            "city": None,
            "warehouse_count": unassigned_warehouses.count(),
            "total_stock_units": total_stock_units,
            "stock_value": str(round(stock_value, 2)),
            "revenue_last_30_days": "0",
        })

    comparison.sort(key=lambda b: b["total_stock_units"], reverse=True)

    return {"branches": comparison}

def compare_warehouse_performance():
    warehouses = Warehouse.objects.filter(is_active=True)
    comparison = []

    for warehouse in warehouses:
        batches = Batch.objects.filter(warehouse=warehouse, is_active=True, quantity__gt=0)
        total_stock_units = sum(b.quantity for b in batches)
        stock_value = sum(b.quantity * (b.unit_cost or b.product.cost_price) for b in batches)

        movements_30d = StockMovement.objects.filter(
            warehouse=warehouse,
            timestamp__gte=timezone.now() - timedelta(days=30),
        ).count()

        active_alerts = Alert.objects.filter(warehouse=warehouse, is_resolved=False).count()

        comparison.append({
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_type": warehouse.warehouse_type,
            "total_stock_units": total_stock_units,
            "stock_value": str(round(stock_value, 2)),
            "movements_last_30_days": movements_30d,
            "active_alerts": active_alerts,
        })

    comparison.sort(key=lambda w: w["total_stock_units"], reverse=True)

    return {"warehouses": comparison}

def _kpi_revenue_30d():
    thirty_days_ago = timezone.now() - timedelta(days=30)
    total = SaleLine.objects.filter(sale__created_at__gte=thirty_days_ago).aggregate(
        total=Sum("line_total")
    )["total"] or 0
    return {"label": "Revenue (Last 30 Days)", "value": str(total)}


def _kpi_active_alerts():
    return {"label": "Active Alerts", "value": Alert.objects.filter(is_resolved=False).count()}


def _kpi_critical_alerts():
    return {"label": "Critical Alerts", "value": Alert.objects.filter(is_resolved=False, severity="critical").count()}


def _kpi_low_stock_count():
    return {
        "label": "Low Stock Alerts",
        "value": Alert.objects.filter(is_resolved=False, alert_type__in=["reorder", "critical", "out_of_stock"]).count(),
    }


def _kpi_sales_today():
    today = timezone.now().date()
    today_sales = Sale.objects.filter(created_at__date=today)
    return {
        "label": "Sales Today",
        "value": today_sales.count(),
        "revenue": str(today_sales.aggregate(total=Sum("total"))["total"] or 0),
    }


def _kpi_active_vendors():
    return {"label": "Active Vendors", "value": Vendor.objects.filter(status="active").count()}


def _kpi_total_inventory_value():
    result = calculate_inventory_valuation(method="weighted_average")
    return {"label": "Total Inventory Value", "value": result["total_inventory_value"]}


KPI_REGISTRY = {
    "revenue_30d": _kpi_revenue_30d,
    "active_alerts": _kpi_active_alerts,
    "critical_alerts": _kpi_critical_alerts,
    "low_stock_count": _kpi_low_stock_count,
    "sales_today": _kpi_sales_today,
    "active_vendors": _kpi_active_vendors,
    "total_inventory_value": _kpi_total_inventory_value,
}


def calculate_selected_kpis(kpi_keys):
    results = {}
    for key in kpi_keys:
        if key in KPI_REGISTRY:
            results[key] = KPI_REGISTRY[key]()
        else:
            results[key] = {"error": "Unknown KPI key"}
    return results


def calculate_inventory_valuation(method="weighted_average"):
    """
    Returns current inventory valuation across all active products.
    method: 'weighted_average' or 'fifo'
    Both use each batch's own stored unit_cost, not a single
    product-wide cost — this is what makes them genuinely meaningful.
    """
    products = Product.objects.filter(is_active=True)
    valuations = []
    total_value = 0

    for product in products:
        batches = Batch.objects.filter(
            product=product, is_active=True, quantity__gt=0
        ).order_by("received_date")

        if not batches.exists():
            continue

        total_quantity = sum(b.quantity for b in batches)

        if method == "weighted_average":
            value = sum(b.quantity * (b.unit_cost or product.cost_price) for b in batches)

        elif method == "fifo":
            # Value stock as if the OLDEST batches are what's still on hand —
            # walk batches oldest-first, using each batch's own real cost
            value = 0
            for batch in batches:
                cost = batch.unit_cost or product.cost_price
                value += batch.quantity * cost

        else:
            continue

        valuations.append({
            "product_sku": product.sku,
            "product_name": product.name,
            "total_quantity": total_quantity,
            "total_value": str(round(value, 2)),
            "batch_breakdown": [
                {
                    "lot_number": b.lot_number,
                    "quantity": b.quantity,
                    "unit_cost": str(b.unit_cost or product.cost_price),
                    "received_date": b.received_date.isoformat(),
                }
                for b in batches
            ],
        })
        total_value += value

    return {
        "method": method,
        "products": valuations,
        "total_inventory_value": str(round(total_value, 2)),
    }
    
def generate_performance_summary(period_days=7):
    from sales.models import Sale, SaleLine
    from vendors.models import Vendor
    from alerts.models import Alert

    cutoff = timezone.now() - timedelta(days=period_days)

    sales_qs = Sale.objects.filter(created_at__gte=cutoff)
    total_revenue = SaleLine.objects.filter(sale__created_at__gte=cutoff).aggregate(
        total=Sum("line_total")
    )["total"] or 0
    total_transactions = sales_qs.count()

    new_alerts = Alert.objects.filter(created_at__gte=cutoff)
    critical_count = new_alerts.filter(severity="critical").count()
    reorder_count = new_alerts.filter(alert_type="reorder").count()
    expiry_count = new_alerts.filter(alert_type="expiry").count()

    top_vendor = Vendor.objects.filter(performance_score__isnull=False).order_by("-performance_score").first()

    valuation = calculate_inventory_valuation(method="weighted_average")
    total_inventory_value = valuation["total_inventory_value"]

    lines = []
    lines.append(f"Performance Summary — Last {period_days} Days")
    lines.append("")

    if total_transactions > 0:
        lines.append(f"Sales: {total_transactions} transaction(s) recorded, generating {total_revenue} in revenue.")
    else:
        lines.append("Sales: No transactions recorded in this period.")

    if new_alerts.exists():
        alert_summary = f"Alerts: {new_alerts.count()} new alert(s) raised"
        details = []
        if critical_count:
            details.append(f"{critical_count} critical")
        if reorder_count:
            details.append(f"{reorder_count} reorder")
        if expiry_count:
            details.append(f"{expiry_count} expiry-related")
        if details:
            alert_summary += f" ({', '.join(details)})."
        else:
            alert_summary += "."
        lines.append(alert_summary)
    else:
        lines.append("Alerts: No new alerts this period — stock levels and expiry dates remained within normal thresholds.")

    if top_vendor:
        lines.append(f"Top-performing vendor: {top_vendor.name}, with a performance score of {top_vendor.performance_score}.")
    else:
        lines.append("Vendor performance: Not enough completed orders yet to score any vendor.")

    lines.append(f"Total inventory currently valued at {total_inventory_value}.")

    return {
        "period_days": period_days,
        "generated_at": timezone.now().isoformat(),
        "summary_text": "\n".join(lines),
        "raw_data": {
            "total_revenue": str(total_revenue),
            "total_transactions": total_transactions,
            "new_alerts": new_alerts.count(),
            "critical_alerts": critical_count,
            "top_vendor": top_vendor.name if top_vendor else None,
            "total_inventory_value": total_inventory_value,
        },
    }