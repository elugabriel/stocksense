import requests
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate
from core.models import Product
from .models import SaleLine
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate

AI_ENGINE_URL = getattr(settings, "AI_ENGINE_URL", "http://127.0.0.1:8001")

# def compare_warehouse_performance():
#     warehouses = Warehouse.objects.filter(is_active=True)
#     comparison = []

#     for warehouse in warehouses:
#         batches = Batch.objects.filter(warehouse=warehouse, is_active=True, quantity__gt=0)
#         total_stock_units = sum(b.quantity for b in batches)
#         stock_value = sum(b.quantity * (b.unit_cost or b.product.cost_price) for b in batches)

#         movements_30d = StockMovement.objects.filter(
#             warehouse=warehouse,
#             timestamp__gte=timezone.now() - timedelta(days=30),
#         ).count()

#         active_alerts = Alert.objects.filter(warehouse=warehouse, is_resolved=False).count()

#         comparison.append({
#             "warehouse_id": warehouse.id,
#             "warehouse_name": warehouse.name,
#             "warehouse_type": warehouse.warehouse_type,
#             "total_stock_units": total_stock_units,
#             "stock_value": str(round(stock_value, 2)),
#             "movements_last_30_days": movements_30d,
#             "active_alerts": active_alerts,
#         })

#     comparison.sort(key=lambda w: w["total_stock_units"], reverse=True)

#     return {"warehouses": comparison}


def get_forecast_vs_actual(product, days_back=30):
    """
    Compares what a forecast would have predicted for the last `days_back`
    days against what actually sold in that same window. Uses whatever
    sales history existed BEFORE that window as the basis for the forecast,
    so this is a genuine backtest, not the forecast peeking at its own answer.
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_back)

    historical_lines = (
        SaleLine.objects.filter(product=product, sale__created_at__date__lt=cutoff_date)
        .annotate(date=TruncDate("sale__created_at"))
        .values("date")
        .annotate(quantity=Sum("quantity"))
        .order_by("date")
    )
    history = [{"date": row["date"].isoformat(), "quantity": row["quantity"]} for row in historical_lines]

    if len(history) < 2:
        return {
            "product_sku": product.sku,
            "error": "Not enough sales history before the comparison window to generate a forecast.",
        }

    try:
        response = requests.post(
            f"{AI_ENGINE_URL}/forecast",
            json={"product_sku": product.sku, "history": history, "forecast_days": days_back},
            timeout=10,
        )
        response.raise_for_status()
        forecast_response = response.json()
    except requests.RequestException as e:
        return {"product_sku": product.sku, "error": f"AI Engine unreachable: {str(e)}"}

    if "error" in forecast_response:
        return {"product_sku": product.sku, "error": forecast_response["error"]}

    predicted_by_date = {p["date"]: p["predicted_quantity"] for p in forecast_response["predictions"]}

    actual_lines = (
        SaleLine.objects.filter(product=product, sale__created_at__date__gte=cutoff_date)
        .annotate(date=TruncDate("sale__created_at"))
        .values("date")
        .annotate(quantity=Sum("quantity"))
        .order_by("date")
    )
    actual_by_date = {row["date"].isoformat(): row["quantity"] for row in actual_lines}

    all_dates = sorted(set(predicted_by_date.keys()) | set(actual_by_date.keys()))
    overlay = [
        {
            "date": d,
            "predicted": predicted_by_date.get(d, 0),
            "actual": actual_by_date.get(d, 0),
        }
        for d in all_dates
    ]

    total_predicted = sum(o["predicted"] for o in overlay)
    total_actual = sum(o["actual"] for o in overlay)
    accuracy_note = None
    if total_actual > 0:
        error_pct = abs(total_predicted - total_actual) / total_actual * 100
        accuracy_note = f"Total forecast was off by {round(error_pct, 1)}% over this period."

    return {
        "product_sku": product.sku,
        "model_used": forecast_response.get("model_used"),
        "days_compared": days_back,
        "total_predicted": total_predicted,
        "total_actual": total_actual,
        "accuracy_note": accuracy_note,
        "overlay": overlay,
    }


def get_forecasted_revenue(product, forecast_days=30):
    forecast_response = get_forecast_for_product(product, forecast_days=forecast_days)

    if "error" in forecast_response:
        return {
            "product_sku": product.sku,
            "error": forecast_response["error"],
        }

    predictions = forecast_response.get("predictions", [])
    total_predicted_units = sum(p["predicted_quantity"] for p in predictions)
    projected_revenue = total_predicted_units * float(product.selling_price)

    return {
        "product_sku": product.sku,
        "product_name": product.name,
        "model_used": forecast_response.get("model_used"),
        "forecast_days": forecast_days,
        "predicted_units": round(total_predicted_units, 1),
        "unit_selling_price": str(product.selling_price),
        "projected_revenue": round(projected_revenue, 2),
        "daily_breakdown": predictions,
    }

def get_forecast_for_product(product, forecast_days=30):
    daily_sales = (
        SaleLine.objects.filter(product=product)
        .annotate(date=TruncDate("sale__created_at"))
        .values("date")
        .annotate(quantity=Sum("quantity"))
        .order_by("date")
    )

    history = [
        {"date": row["date"].isoformat(), "quantity": row["quantity"]}
        for row in daily_sales
    ]

    try:
        response = requests.post(
            f"{AI_ENGINE_URL}/forecast",
            json={
                "product_sku": product.sku,
                "history": history,
                "forecast_days": forecast_days,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"AI Engine unreachable: {str(e)}"}