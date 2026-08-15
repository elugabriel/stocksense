from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import UserViewSet, CustomerRegisterView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("auth/register/", CustomerRegisterView.as_view(), name="customer-register"),
] + router.urls