from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from accounts.permissions import IsScopedToLocation
from django.db.models import Sum
from rest_framework.views import APIView


from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Batch, StockMovement, Product, Warehouse, StockTransfer, Category, StockAdjustment
from .serializers import (
    ProductSerializer, AddStockSerializer, ReceiveStockFromVendorSerializer,
    ReturnStockSerializer, TransferStockSerializer, RemoveDamagedExpiredSerializer,
    PhysicalCountSerializer, WarehouseSerializer, CategorySerializer,
    StockMovementSerializer,
)
from .services import calculate_inventory_valuation

from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from sales.models import Sale, SaleLine
from alerts.models import Alert
from vendors.models import Vendor


from .models import DashboardPreference
from .services import calculate_selected_kpis, KPI_REGISTRY


from .services import compare_warehouse_performance

from .services import compare_branch_performance

from .services import generate_performance_summary


class PerformanceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        result = generate_performance_summary(period_days=days)
        return Response(result)
class BranchPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = compare_branch_performance()
        return Response(result)

class WarehousePerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = compare_warehouse_performance()
        return Response(result)

class DashboardKPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pref, _ = DashboardPreference.objects.get_or_create(user=request.user)
        selected = pref.selected_kpis or list(KPI_REGISTRY.keys())[:4]  # sensible default
        results = calculate_selected_kpis(selected)
        return Response({
            "available_kpis": list(KPI_REGISTRY.keys()),
            "selected_kpis": selected,
            "kpi_data": results,
        })

    def post(self, request):
        kpi_keys = request.data.get("selected_kpis", [])
        invalid = [k for k in kpi_keys if k not in KPI_REGISTRY]
        if invalid:
            return Response({"detail": f"Unknown KPI keys: {invalid}"}, status=400)

        pref, _ = DashboardPreference.objects.get_or_create(user=request.user)
        pref.selected_kpis = kpi_keys
        pref.save()
        return Response({"message": "Dashboard preferences saved", "selected_kpis": kpi_keys})


class RoleAwareDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = user.role

        base_data = {
            "user_role": role,
            "role_display": user.get_role_display(),
        }

        if role in ["super_admin", "org_admin", "executive"]:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            revenue = SaleLine.objects.filter(sale__created_at__gte=thirty_days_ago).aggregate(
                total=Sum("line_total")
            )["total"] or 0
            active_alerts = Alert.objects.filter(is_resolved=False).count()
            critical_alerts = Alert.objects.filter(is_resolved=False, severity="critical").count()
            vendor_count = Vendor.objects.filter(status="active").count()

            base_data.update({
                "view_type": "executive",
                "revenue_last_30_days": str(revenue),
                "active_alerts": active_alerts,
                "critical_alerts": critical_alerts,
                "active_vendors": vendor_count,
            })

        elif role in ["warehouse_manager", "inventory_officer"]:
            low_stock_alerts = Alert.objects.filter(
                is_resolved=False, alert_type__in=["reorder", "critical", "out_of_stock"]
            ).count()
            expiry_alerts = Alert.objects.filter(is_resolved=False, alert_type="expiry").count()

            base_data.update({
                "view_type": "warehouse_operations",
                "low_stock_alerts": low_stock_alerts,
                "expiry_alerts": expiry_alerts,
            })

        elif role == "sales_staff":
            today = timezone.now().date()
            today_sales = Sale.objects.filter(created_at__date=today)
            base_data.update({
                "view_type": "sales_floor",
                "sales_today_count": today_sales.count(),
                "sales_today_revenue": str(today_sales.aggregate(total=Sum("total"))["total"] or 0),
            })

        elif role == "procurement_officer":
            pending_reorder_alerts = Alert.objects.filter(is_resolved=False, alert_type="reorder").count()
            base_data.update({
                "view_type": "procurement",
                "pending_reorder_alerts": pending_reorder_alerts,
                "active_vendors": Vendor.objects.filter(status="active").count(),
            })

        elif role == "accountant":
            thirty_days_ago = timezone.now() - timedelta(days=30)
            revenue = SaleLine.objects.filter(sale__created_at__gte=thirty_days_ago).aggregate(
                total=Sum("line_total")
            )["total"] or 0
            base_data.update({
                "view_type": "financial",
                "revenue_last_30_days": str(revenue),
            })

        else:
            base_data.update({"view_type": "general"})

        return Response(base_data)

class TransferStockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        source_batch = get_object_or_404(Batch, id=data["batch_id"])
        source_warehouse = get_object_or_404(Warehouse, id=data["source_warehouse_id"])
        destination_warehouse = get_object_or_404(Warehouse, id=data["destination_warehouse_id"])
        quantity = data["quantity"]

        if source_warehouse == destination_warehouse:
            return Response(
                {"detail": "Source and destination warehouses must be different"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source_batch.quantity < quantity:
            return Response(
                {"detail": f"Insufficient stock in source batch. Available: {source_batch.quantity}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Reduce stock at source
            source_batch.quantity -= quantity
            source_batch.save()

            # Add stock at destination — same lot number, new or existing batch there
            dest_batch, created = Batch.objects.get_or_create(
                product=product,
                warehouse=destination_warehouse,
                lot_number=source_batch.lot_number,
                defaults={
                    "quantity": quantity,
                    "unit_cost": source_batch.unit_cost,
                    "manufacture_date": source_batch.manufacture_date,
                    "expiry_date": source_batch.expiry_date,
                },
            )
            if not created:
                dest_batch.quantity += quantity
                dest_batch.save()

            # Create the formal transfer record
            transfer = StockTransfer.objects.create(
                product=product,
                batch=source_batch,
                source_warehouse=source_warehouse,
                destination_warehouse=destination_warehouse,
                quantity=quantity,
                status=StockTransfer.Status.COMPLETED,
                initiated_by=request.user,
                notes=data.get("notes", ""),
            )

            # Log both sides of the movement ledger
            StockMovement.objects.create(
                product=product,
                warehouse=source_warehouse,
                batch=source_batch,
                movement_type=StockMovement.MovementType.TRANSFER_OUT,
                quantity=-quantity,
                reference_id=str(transfer.id),
                performed_by=request.user,
                notes=f"Transfer to {destination_warehouse.name}",
            )
            StockMovement.objects.create(
                product=product,
                warehouse=destination_warehouse,
                batch=dest_batch,
                movement_type=StockMovement.MovementType.TRANSFER_IN,
                quantity=quantity,
                reference_id=str(transfer.id),
                performed_by=request.user,
                notes=f"Transfer from {source_warehouse.name}",
            )

        return Response(
            {
                "message": "Transfer completed successfully",
                "transfer_id": transfer.id,
                "source_batch_new_quantity": source_batch.quantity,
                "destination_batch_id": dest_batch.id,
                "destination_batch_new_quantity": dest_batch.quantity,
            },
            status=status.HTTP_201_CREATED,
        )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsScopedToLocation]

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        barcode = request.query_params.get("barcode")
        if not barcode:
            return Response(
                {"detail": "barcode query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            return Response(
                {"detail": "No product found with that barcode"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(product)
        return Response(serializer.data)


class StockDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        by_product = (
            Batch.objects.filter(is_active=True)
            .values("product__sku", "product__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("product__name")
        )

        by_category = (
            Batch.objects.filter(is_active=True)
            .values("product__category__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("product__category__name")
        )

        by_warehouse = (
            Batch.objects.filter(is_active=True)
            .values("warehouse__name", "warehouse__branch__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("warehouse__name")
        )

        return Response({
            "by_product": list(by_product),
            "by_category": list(by_category),
            "by_warehouse": list(by_warehouse),
        })


class AddStockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])

        with transaction.atomic():
            batch, created = Batch.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                lot_number=data["lot_number"],
                defaults={
                    "quantity": data["quantity"],
                    "unit_cost": data.get("unit_cost") or product.cost_price,
                    "manufacture_date": data.get("manufacture_date"),
                    "expiry_date": data.get("expiry_date"),
                },
            )
            if not created:
                batch.quantity += data["quantity"]
                batch.save()

            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                movement_type=StockMovement.MovementType.RECEIVED,
                quantity=data["quantity"],
                performed_by=request.user,
                notes="Stock added via Add Stock endpoint",
            )

        return Response(
            {
                "message": "Stock added successfully",
                "batch_id": batch.id,
                "new_quantity": batch.quantity,
            },
            status=status.HTTP_201_CREATED,
        )


class ReceiveStockFromVendorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReceiveStockFromVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])

        with transaction.atomic():
            batch, created = Batch.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                lot_number=data["lot_number"],
                defaults={
                    "quantity": data["quantity"],
                    "unit_cost": data.get("unit_cost") or product.cost_price,
                    "manufacture_date": data.get("manufacture_date"),
                    "expiry_date": data.get("expiry_date"),
                },
            )
            if not created:
                batch.quantity += data["quantity"]
                batch.save()

            vendor_ref = data.get("vendor_reference", "")
            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                movement_type=StockMovement.MovementType.RECEIVED,
                quantity=data["quantity"],
                reference_id=vendor_ref,
                performed_by=request.user,
                notes=f"Received from vendor. Reference: {vendor_ref or 'N/A'}",
            )

        return Response(
            {
                "message": "Stock received from vendor successfully",
                "batch_id": batch.id,
                "new_quantity": batch.quantity,
            },
            status=status.HTTP_201_CREATED,
        )


class ReturnStockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReturnStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])
        batch = None
        if data.get("batch_id"):
            batch = get_object_or_404(Batch, id=data["batch_id"])

        direction = data["direction"]
        quantity = data["quantity"]

        with transaction.atomic():
            if direction == "to_vendor":
                # Stock leaves — decreasing an existing batch
                if batch:
                    batch.quantity = max(0, batch.quantity - quantity)
                    batch.save()
                movement_quantity = -quantity
                movement_type = StockMovement.MovementType.RETURN
                note = f"Returned to vendor. Reason: {data['reason']}"

            else:  # from_customer
                if data["is_resellable"] and batch:
                    batch.quantity += quantity
                    batch.save()
                    movement_quantity = quantity
                    note = f"Customer return (resellable). Reason: {data['reason']}"
                else:
                    # Not resellable — log it, but don't add back to sellable stock
                    movement_quantity = 0
                    note = f"Customer return (NOT resellable, held for disposal). Reason: {data['reason']}"
                movement_type = StockMovement.MovementType.RETURN

            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                movement_type=movement_type,
                quantity=movement_quantity,
                performed_by=request.user,
                notes=note,
            )

        return Response(
            {
                "message": "Return processed successfully",
                "direction": direction,
                "quantity": quantity,
                "batch_id": batch.id if batch else None,
                "new_quantity": batch.quantity if batch else None,
            },
            status=status.HTTP_200_OK,
        )


class RemoveDamagedExpiredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RemoveDamagedExpiredSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])
        batch = get_object_or_404(Batch, id=data["batch_id"])
        quantity = data["quantity"]

        if batch.quantity < quantity:
            return Response(
                {"detail": f"Cannot remove more than available. Batch has {batch.quantity} units."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            batch.quantity -= quantity
            batch.save()

            adjustment = StockAdjustment.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                quantity_change=-quantity,
                reason_code=data["reason_code"],
                reason_notes=data["reason_notes"],
                requested_by=request.user,
                is_approved=True,
                approved_by=request.user,
            )

            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                movement_type=StockMovement.MovementType.DAMAGE,
                quantity=-quantity,
                reference_id=str(adjustment.id),
                performed_by=request.user,
                notes=f"{data['reason_code']}: {data['reason_notes']}",
            )

        return Response(
            {
                "message": "Damaged/expired stock removed successfully",
                "adjustment_id": adjustment.id,
                "batch_new_quantity": batch.quantity,
            },
            status=status.HTTP_201_CREATED,
        )


class PhysicalCountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PhysicalCountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, id=data["product_id"])
        warehouse = get_object_or_404(Warehouse, id=data["warehouse_id"])
        batch = get_object_or_404(Batch, id=data["batch_id"])
        counted_quantity = data["counted_quantity"]

        system_quantity = batch.quantity
        difference = counted_quantity - system_quantity

        if difference == 0:
            return Response(
                {
                    "message": "Physical count matches system quantity — no adjustment needed",
                    "batch_id": batch.id,
                    "quantity": system_quantity,
                },
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            batch.quantity = counted_quantity
            batch.save()

            adjustment = StockAdjustment.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                quantity_change=difference,
                reason_code=StockAdjustment.ReasonCode.COUNT_CORRECTION,
                reason_notes=data.get("notes", "") or f"Physical count correction: system showed {system_quantity}, counted {counted_quantity}",
                requested_by=request.user,
                is_approved=True,
                approved_by=request.user,
            )

            StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                batch=batch,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity=difference,
                reference_id=str(adjustment.id),
                performed_by=request.user,
                notes=f"Physical count correction: {system_quantity} → {counted_quantity}",
            )

        return Response(
            {
                "message": "Physical count reconciled successfully",
                "adjustment_id": adjustment.id,
                "system_quantity_before": system_quantity,
                "counted_quantity": counted_quantity,
                "difference": difference,
                "batch_new_quantity": batch.quantity,
            },
            status=status.HTTP_201_CREATED,
        )


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all().order_by("-timestamp")
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]


class InventoryValuationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        method = request.query_params.get("method", "weighted_average")
        result = calculate_inventory_valuation(method=method)
        return Response(result)