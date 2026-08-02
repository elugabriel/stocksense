from django.shortcuts import render

# Create your views here.
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Product, Batch, Warehouse, Branch, StockMovement
from .models import Sale, SaleLine
from .serializers import RecordSaleSerializer, SaleSerializer

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta

from .services import get_forecasted_revenue
from core.models import Product



from .services import get_forecast_vs_actual


class ForecastVsActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        days_back = int(request.query_params.get("days", 30))
        result = get_forecast_vs_actual(product, days_back=days_back)
        return Response(result)
    
    
class RevenueReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_by = request.query_params.get("group_by", "product")

        lines = SaleLine.objects.select_related("sale", "product", "product__category")

        if group_by == "product":
            data = (
                lines.values("product__sku", "product__name")
                .annotate(revenue=Sum("line_total"), quantity_sold=Sum("quantity"))
                .order_by("-revenue")
            )
        elif group_by == "category":
            data = (
                lines.values("product__category__name")
                .annotate(revenue=Sum("line_total"), quantity_sold=Sum("quantity"))
                .order_by("-revenue")
            )
        elif group_by == "branch":
            data = (
                lines.values("sale__branch__name")
                .annotate(revenue=Sum("line_total"), quantity_sold=Sum("quantity"))
                .order_by("-revenue")
            )
        else:
            return Response({"detail": "group_by must be one of: product, category, branch"}, status=400)

        return Response({"group_by": group_by, "report": list(data)})

class CustomerTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customers = (
            Sale.objects.exclude(customer_phone="", customer_email="")
            .values("customer_name", "customer_phone", "customer_email")
            .annotate(
                total_spent=Sum("total"),
                order_count=Count("id"),
            )
            .order_by("-total_spent")
        )

        return Response({"customers": list(customers)})




class ProductSalesHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        lines = (
            SaleLine.objects.filter(product_id=product_id)
            .select_related("sale")
            .order_by("-sale__created_at")
        )

        history = [
            {
                "sale_number": line.sale.sale_number,
                "date": line.sale.created_at.date().isoformat(),
                "quantity": line.quantity,
                "unit_price": str(line.unit_price),
                "line_total": str(line.line_total),
                "customer_name": line.sale.customer_name,
            }
            for line in lines
        ]

        totals = lines.aggregate(
            total_quantity_sold=Sum("quantity"),
            total_revenue=Sum("line_total"),
        )

        return Response({
            "product_id": product_id,
            "total_quantity_sold": totals["total_quantity_sold"] or 0,
            "total_revenue": str(totals["total_revenue"] or 0),
            "transaction_count": lines.count(),
            "history": history,
        })
        
        
class SalesSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        days_back = int(request.query_params.get("days", 30))

        cutoff = timezone.now() - timedelta(days=days_back)
        queryset = Sale.objects.filter(created_at__gte=cutoff)

        trunc_map = {
            "daily": TruncDate("created_at"),
            "weekly": TruncWeek("created_at"),
            "monthly": TruncMonth("created_at"),
        }
        trunc_fn = trunc_map.get(period, TruncDate("created_at"))

        summary = (
            queryset
            .annotate(period_start=trunc_fn)
            .values("period_start")
            .annotate(
                total_revenue=Sum("total"),
                transaction_count=Count("id"),
            )
            .order_by("period_start")
        )

        return Response({
            "period": period,
            "days_covered": days_back,
            "summary": list(summary),
        })
        
        
class RecordSaleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])
        branch = None
        if data.get("branch_id"):
            branch = get_object_or_404(Branch, id=data["branch_id"])

        with transaction.atomic():
            subtotal = 0
            sale = Sale.objects.create(
                sale_number=data["sale_number"],
                branch=branch,
                warehouse=warehouse,
                customer_name=data.get("customer_name", ""),
                customer_phone=data.get("customer_phone", ""),
                customer_email=data.get("customer_email", ""),
                payment_method=data["payment_method"],
                sold_by=request.user,
                discount=data.get("discount", 0),
                notes=data.get("notes", ""),
            )

            for line_data in data["lines"]:
                product = get_object_or_404(Product, id=line_data["product_id"])
                batch = None
                if line_data.get("batch_id"):
                    batch = get_object_or_404(Batch, id=line_data["batch_id"])

                quantity = line_data["quantity"]

                if batch:
                    if batch.quantity < quantity:
                        raise ValueError(f"Insufficient stock for {product.sku} in batch {batch.lot_number}")
                    batch.quantity -= quantity
                    batch.save()

                line_total = line_data["unit_price"] * quantity
                subtotal += line_total

                SaleLine.objects.create(
                    sale=sale,
                    product=product,
                    batch=batch,
                    quantity=quantity,
                    unit_price=line_data["unit_price"],
                    line_total=line_total,
                )

                StockMovement.objects.create(
                    product=product,
                    warehouse=warehouse,
                    batch=batch,
                    movement_type=StockMovement.MovementType.SALE,
                    quantity=-quantity,
                    reference_id=str(sale.id),
                    performed_by=request.user,
                    notes=f"Sale {sale.sale_number}",
                )

            sale.subtotal = subtotal
            sale.total = subtotal - sale.discount
            sale.save()

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.all().order_by("-created_at")
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    
class ProfitMarginReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        days_back = int(request.query_params.get("days", 30))

        cutoff = timezone.now() - timedelta(days=days_back)

        lines = (
            SaleLine.objects.filter(sale__created_at__gte=cutoff)
            .select_related("product", "sale")
        )

        trunc_map = {
            "daily": TruncDate("sale__created_at"),
            "weekly": TruncWeek("sale__created_at"),
            "monthly": TruncMonth("sale__created_at"),
        }
        trunc_fn = trunc_map.get(period, TruncDate("sale__created_at"))

        report_data = {}
        for line in lines.annotate(period_start=trunc_fn):
            key = line.period_start
            if key not in report_data:
                report_data[key] = {"revenue": 0, "cost": 0, "quantity": 0}

            revenue = line.line_total
            cost = line.product.cost_price * line.quantity

            report_data[key]["revenue"] += revenue
            report_data[key]["cost"] += cost
            report_data[key]["quantity"] += line.quantity

        results = []
        for period_start, data in sorted(report_data.items()):
            profit = data["revenue"] - data["cost"]
            margin_percent = (profit / data["revenue"] * 100) if data["revenue"] > 0 else 0
            results.append({
                "period_start": period_start.isoformat(),
                "revenue": str(data["revenue"]),
                "cost": str(data["cost"]),
                "profit": str(profit),
                "gross_margin_percent": round(margin_percent, 1),
                "units_sold": data["quantity"],
            })

        return Response({"period": period, "days_covered": days_back, "report": results})
    
    

class ForecastedRevenueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        forecast_days = int(request.query_params.get("forecast_days", 30))
        result = get_forecasted_revenue(product, forecast_days=forecast_days)
        return Response(result)