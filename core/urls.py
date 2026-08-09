from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, StockDashboardView, AddStockView,
    ReceiveStockFromVendorView, ReturnStockView, TransferStockView,
    RemoveDamagedExpiredView, PhysicalCountView,
    WarehouseViewSet, CategoryViewSet,
    StockMovementViewSet, InventoryValuationView,
    RoleAwareDashboardView, DashboardKPIView,
    WarehousePerformanceView, BranchPerformanceView,
    PerformanceSummaryView,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"movements", StockMovementViewSet, basename="movement")

urlpatterns = [
    path("performance-summary/", PerformanceSummaryView.as_view(), name="performance-summary"),
    path("branches/performance/", BranchPerformanceView.as_view(), name="branch-performance"),
    path("warehouses/performance/", WarehousePerformanceView.as_view(), name="warehouse-performance"),
    path("dashboard/kpis/", DashboardKPIView.as_view(), name="dashboard-kpis"),
    path("dashboard/role-aware/", RoleAwareDashboardView.as_view(), name="role-aware-dashboard"),
    path("dashboard/stock/", StockDashboardView.as_view(), name="stock-dashboard"),
    path("stock/add/", AddStockView.as_view(), name="add-stock"),
    path("stock/receive/", ReceiveStockFromVendorView.as_view(), name="receive-stock"),
    path("stock/return/", ReturnStockView.as_view(), name="return-stock"),
    path("stock/transfer/", TransferStockView.as_view(), name="transfer-stock"),
    path("stock/remove-damaged/", RemoveDamagedExpiredView.as_view(), name="remove-damaged-stock"),
    path("stock/physical-count/", PhysicalCountView.as_view(), name="physical-count"),
    path("inventory/valuation/", InventoryValuationView.as_view(), name="inventory-valuation"),
] + router.urls