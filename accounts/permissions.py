from rest_framework import permissions


class IsScopedToLocation(permissions.BasePermission):
    """
    Super Admins, Org Admins, and Executives see everything.
    Everyone else is restricted to their assigned branch/warehouse.
    """

    UNRESTRICTED_ROLES = {"super_admin", "org_admin", "executive"}

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in self.UNRESTRICTED_ROLES:
            return True

        obj_warehouse = getattr(obj, "warehouse", None)
        obj_branch = getattr(obj, "branch", None)

        if user.warehouse and obj_warehouse:
            return obj_warehouse == user.warehouse

        if user.branch and obj_branch:
            return obj_branch == user.branch

        return False