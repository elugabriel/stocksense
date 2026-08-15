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

        # If the object has no warehouse/branch to scope against at all,
        # it isn't location-specific data — don't block access to it.
        if obj_warehouse is None and obj_branch is None:
            return True

        if user.warehouse and obj_warehouse:
            return obj_warehouse == user.warehouse

        if user.branch and obj_branch:
            return obj_branch == user.branch

        return False
    
class IsStaffUser(permissions.BasePermission):
    """
    Blocks customers from staff-only endpoints. Any authenticated role
    except 'customer' is considered staff for this check.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role != "customer"