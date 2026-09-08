from rest_framework.permissions import BasePermission

class IsOrderManagementStaff(BasePermission):
    """
    Allows access only to users who can manage orders.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = (
            request.user.Role.ADMIN,
            request.user.Role.MANAGER,
            request.user.Role.STAFF,
        )

        return request.user.role in allowed_roles