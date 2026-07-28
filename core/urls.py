from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet, StockDashboardView, AddStockView,
    ReceiveStockFromVendorView, ReturnStockView, TransferStockView,
    RemoveDamagedExpiredView, PhysicalCountView,
    WarehouseViewSet, CategoryViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"movements", StockMovementViewSet, basename="movement")





urlpatterns = router.urls + [
    path("dashboard/stock/", StockDashboardView.as_view(), name="stock-dashboard"),
    path("stock/add/", AddStockView.as_view(), name="add-stock"),
    path("stock/receive/", ReceiveStockFromVendorView.as_view(), name="receive-stock"),
    path("stock/return/", ReturnStockView.as_view(), name="return-stock"),
    path("stock/transfer/", TransferStockView.as_view(), name="transfer-stock"),
    path("stock/remove-damaged/", RemoveDamagedExpiredView.as_view(), name="remove-damaged-stock"),
    path("stock/physical-count/", PhysicalCountView.as_view(), name="physical-count"),
]