import requests
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate
from core.models import Product
from .models import SaleLine


AI_ENGINE_URL = getattr(settings, "AI_ENGINE_URL", "http://127.0.0.1:8001")





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