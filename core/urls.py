from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockDashboardView

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = router.urls + [
    path("dashboard/stock/", StockDashboardView.as_view(), name="stock-dashboard"),
]