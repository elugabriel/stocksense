"""
URL configuration for stocksense project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import RateLimitedTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/login/', RateLimitedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('core.urls')),
    path('api/v1/', include('alerts.urls')),
    path('api/v1/', include('vendors.urls')),
    path('api/v1/', include('sales.urls')),
]