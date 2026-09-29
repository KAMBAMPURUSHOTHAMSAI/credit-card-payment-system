from rest_framework.permissions import BasePermission


class IsAdminUserCustom(
    BasePermission
):
    """
    Allows only staff/admin users.
    """

    def has_permission(
        self,
        request,
        view,
    ):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )