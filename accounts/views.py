from django.shortcuts import render

# Create your views here.
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView


from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer, CreateUserSerializer



@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class RateLimitedTokenObtainPairView(TokenObtainPairView):
    pass



class IsSuperAdminOrOrgAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role in ["super_admin", "org_admin"]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    permission_classes = [IsSuperAdminOrOrgAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return UserSerializer