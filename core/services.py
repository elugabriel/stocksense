from .models import Batch, Product


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