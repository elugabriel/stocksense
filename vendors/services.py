from django.utils import timezone
from django.db.models import F
from .models import Vendor, PurchaseOrder

from django.db.models import Sum, Avg
from .models import Vendor, PurchaseOrderLine


def get_best_vendor_for_product(product):
    """
    Finds every vendor who has supplied this product before, ranked by
    performance_score. Falls back to average unit cost if no vendor has
    a score yet (e.g. too few orders for Phase 8's scoring to apply).
    """
    lines = PurchaseOrderLine.objects.filter(product=product).select_related(
        "purchase_order__vendor"
    )

    vendor_ids = set(line.purchase_order.vendor_id for line in lines)

    if not vendor_ids:
        return {
            "product_sku": product.sku,
            "error": "No vendor has ever supplied this product. No purchase order history to base a recommendation on.",
        }

    vendors_data = []
    for vendor_id in vendor_ids:
        vendor = Vendor.objects.get(id=vendor_id)
        vendor_lines = lines.filter(purchase_order__vendor_id=vendor_id)

        total_ordered = vendor_lines.aggregate(total=Sum("quantity_ordered"))["total"] or 0
        avg_unit_cost = vendor_lines.aggregate(avg=Avg("unit_cost"))["avg"] or 0

        vendors_data.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "performance_score": float(vendor.performance_score) if vendor.performance_score is not None else None,
            "average_unit_cost": round(float(avg_unit_cost), 2),
            "total_units_previously_ordered": total_ordered,
            "quoted_lead_time_days": vendor.default_lead_time_days,
        })

    scored = [v for v in vendors_data if v["performance_score"] is not None]
    unscored = [v for v in vendors_data if v["performance_score"] is None]

    scored.sort(key=lambda v: v["performance_score"], reverse=True)
    # Vendors with no score yet get sorted by lowest cost as a fallback signal
    unscored.sort(key=lambda v: v["average_unit_cost"])

    ranked = scored + unscored
    best = ranked[0] if ranked else None

    return {
        "product_sku": product.sku,
        "recommended_vendor": best,
        "all_vendors_considered": ranked,
        "note": "Ranked by performance score where available; vendors without a score yet are ranked by lowest average cost as a fallback." if unscored else None,
    }

def calculate_vendor_score(vendor):
    """
    Simple weighted score out of 100:
    - 70% weight on on-time delivery rate
    - 30% weight on how close actual lead time is to quoted lead time
      (penalizes both being much slower AND wildly inconsistent)
    Returns None if there isn't enough order history to score fairly.
    """
    received_orders = vendor.purchase_orders.filter(
        status=PurchaseOrder.Status.RECEIVED,
        actual_delivery_date__isnull=False,
    )

    received_count = received_orders.count()
    if received_count < 1:
        return None

    on_time_count = received_orders.filter(
        actual_delivery_date__lte=F("expected_delivery_date")
    ).count()
    on_time_rate = on_time_count / received_count

    if vendor.default_lead_time_days:
        lead_times = [
            (po.actual_delivery_date - po.created_at.date()).days
            for po in received_orders
            if po.actual_delivery_date and po.created_at
        ]
        avg_lead_time = sum(lead_times) / len(lead_times)
        accuracy_ratio = min(vendor.default_lead_time_days / avg_lead_time, 1) if avg_lead_time > 0 else 1
    else:
        accuracy_ratio = 0.5  # neutral score if no quoted lead time to compare against

    score = (on_time_rate * 70) + (accuracy_ratio * 30)
    return round(score, 2)


def update_vendor_score(vendor):
    score = calculate_vendor_score(vendor)
    vendor.performance_score = score
    vendor.performance_score_updated_at = timezone.now()
    vendor.save(update_fields=["performance_score", "performance_score_updated_at"])
    return score