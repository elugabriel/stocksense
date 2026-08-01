from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    SaleViewSet, RecordSaleView, SalesSummaryView,
    ProductSalesHistoryView, CustomerTrendsView, RevenueReportView,
    ProfitMarginReportView, ForecastedRevenueView,
)

router = DefaultRouter()
router.register(r"sales", SaleViewSet, basename="sale")





urlpatterns = [
    path("sales/record/", RecordSaleView.as_view(), name="record-sale"),
    path("sales/summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("sales/customer-trends/", CustomerTrendsView.as_view(), name="customer-trends"),
    path("sales/revenue-report/", RevenueReportView.as_view(), name="revenue-report"),
    path("sales/profit-margin-report/", ProfitMarginReportView.as_view(), name="profit-margin-report"),
    path("products/<int:product_id>/sales-history/", ProductSalesHistoryView.as_view(), name="product-sales-history"),
    path("products/<int:product_id>/forecasted-revenue/", ForecastedRevenueView.as_view(), name="forecasted-revenue"),
] + router.urls