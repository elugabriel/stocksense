from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet, BestVendorForProductView

router = DefaultRouter()
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchase-order")

urlpatterns = [
    path("products/<int:product_id>/best-vendor/", BestVendorForProductView.as_view(), name="best-vendor"),
] + router.urls