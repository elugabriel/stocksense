from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Scope", {"fields": ("role", "branch", "warehouse")}),
    )
    list_display = ("username", "email", "role", "branch", "warehouse", "is_staff")


admin.site.register(User, CustomUserAdmin)