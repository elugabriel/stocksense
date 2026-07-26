from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Product
from .serializers import ProductSerializer
from accounts.permissions import IsScopedToLocation


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

from django.db.models import Sum
from rest_framework.views import APIView

from .models import Batch


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