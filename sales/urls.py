from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    SaleViewSet, RecordSaleView, SalesSummaryView,
    ProductSalesHistoryView, CustomerTrendsView, RevenueReportView,
    ProfitMarginReportView, ForecastedRevenueView, ForecastVsActualView,
    PlaceOrderView, MyOrdersView, ConfirmOrderView, FulfillOrderView,
)


router = DefaultRouter()
router.register(r"sales", SaleViewSet, basename="sale")





urlpatterns = [
    path("orders/place/", PlaceOrderView.as_view(), name="place-order"),
    path("orders/mine/", MyOrdersView.as_view(), name="my-orders"),
    path("orders/<int:order_id>/confirm/", ConfirmOrderView.as_view(), name="confirm-order"),
    path("orders/<int:order_id>/fulfill/", FulfillOrderView.as_view(), name="fulfill-order"),
    path("products/<int:product_id>/forecast-vs-actual/", ForecastVsActualView.as_view(), name="forecast-vs-actual"),
    path("sales/record/", RecordSaleView.as_view(), name="record-sale"),
    path("sales/summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("sales/customer-trends/", CustomerTrendsView.as_view(), name="customer-trends"),
    path("sales/revenue-report/", RevenueReportView.as_view(), name="revenue-report"),
    path("sales/profit-margin-report/", ProfitMarginReportView.as_view(), name="profit-margin-report"),
    path("products/<int:product_id>/sales-history/", ProductSalesHistoryView.as_view(), name="product-sales-history"),
    path("products/<int:product_id>/forecasted-revenue/", ForecastedRevenueView.as_view(), name="forecasted-revenue"),
] + router.urls