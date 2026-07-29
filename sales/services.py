import requests
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate

from .models import SaleLine


AI_ENGINE_URL = getattr(settings, "AI_ENGINE_URL", "http://127.0.0.1:8001")


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