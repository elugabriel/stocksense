from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchase-order")

urlpatterns = router.urls