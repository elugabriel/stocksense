from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import User


class CustomUserAdmin(SimpleHistoryAdmin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Scope", {"fields": ("role", "branch", "warehouse")}),
    )
    list_display = ("username", "email", "role", "branch", "warehouse", "is_staff")


admin.site.register(User, CustomUserAdmin)