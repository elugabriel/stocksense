from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F

from .models import Vendor, PurchaseOrder, PurchaseOrderLine
from .serializers import VendorSerializer, PurchaseOrderSerializer


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def purchase_history(self, request, pk=None):
        vendor = self.get_object()
        orders = vendor.purchase_orders.all().order_by("-created_at")
        serializer = PurchaseOrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None):
        vendor = self.get_object()
        received_orders = vendor.purchase_orders.filter(
            status=PurchaseOrder.Status.RECEIVED,
            actual_delivery_date__isnull=False,
        )

        total_orders = vendor.purchase_orders.count()
        received_count = received_orders.count()

        on_time_count = received_orders.filter(
            actual_delivery_date__lte=F("expected_delivery_date")
        ).count()

        on_time_rate = (on_time_count / received_count * 100) if received_count else None

        lead_times = []
        for po in received_orders:
            if po.actual_delivery_date and po.created_at:
                delta = (po.actual_delivery_date - po.created_at.date()).days
                lead_times.append(delta)

        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else None

        return Response({
            "vendor": vendor.name,
            "total_orders": total_orders,
            "received_orders": received_count,
            "on_time_deliveries": on_time_count,
            "on_time_rate_percent": round(on_time_rate, 1) if on_time_rate is not None else None,
            "average_lead_time_days": round(avg_lead_time, 1) if avg_lead_time is not None else None,
            "quoted_lead_time_days": vendor.default_lead_time_days,
        })

    @action(detail=True, methods=["get"])
    def cost_trends(self, request, pk=None):
        vendor = self.get_object()
        lines = PurchaseOrderLine.objects.filter(
            purchase_order__vendor=vendor
        ).select_related("product", "purchase_order").order_by("purchase_order__created_at")

        trend_data = [
            {
                "product_sku": line.product.sku,
                "product_name": line.product.name,
                "unit_cost": str(line.unit_cost),
                "order_number": line.purchase_order.order_number,
                "order_date": line.purchase_order.created_at.date().isoformat(),
            }
            for line in lines
        ]

        return Response({"vendor": vendor.name, "cost_history": trend_data})


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by("-created_at")
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)