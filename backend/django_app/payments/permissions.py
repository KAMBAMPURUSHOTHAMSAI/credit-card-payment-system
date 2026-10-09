
from rest_framework.permissions import BasePermission, SAFE_METHODS


# =========================================================
# APPLICATION ROLE NAMES
# =========================================================

ROLE_ADMIN = "Admin"
ROLE_SUPPORT = "Support"
ROLE_READ_ONLY = "Read-Only"

APPLICATION_ROLE_NAMES = {
    ROLE_ADMIN,
    ROLE_SUPPORT,
    ROLE_READ_ONLY,
}


# =========================================================
# ROLE HELPER FUNCTIONS
# =========================================================

def get_user_roles(user):
    """
    Return recognized application roles assigned through
    Django Groups.
    """

    if not user or not user.is_authenticated:
        return set()

    return set(
        user.groups
        .filter(name__in=APPLICATION_ROLE_NAMES)
        .values_list("name", flat=True)
    )


def user_has_any_role(user, required_roles):
    """
    Require explicit application-role assignment.
    Superusers retain full access.

    is_staff controls Django Admin site access; it does
    not automatically grant application API permissions.
    """

    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    assigned_roles = get_user_roles(user)

    return bool(assigned_roles.intersection(required_roles))


# =========================================================
# ADMIN ONLY
# =========================================================

class IsAdminUserCustom(BasePermission):
    """Allow Admin role users and superusers only."""

    message = "Administrator permission is required."

    def has_permission(self, request, view):
        return user_has_any_role(
            request.user,
            {ROLE_ADMIN},
        )


# =========================================================
# ADMIN OR SUPPORT
# =========================================================

class IsAdminOrSupportUserCustom(BasePermission):
    """Allow Admin and Support role users."""

    message = "Admin or Support permission is required."

    def has_permission(self, request, view):
        return user_has_any_role(
            request.user,
            {
                ROLE_ADMIN,
                ROLE_SUPPORT,
            },
        )


# =========================================================
# APPLICATION ROLE ACCESS
# =========================================================

class IsApplicationRoleUserCustom(BasePermission):
    """
    Allow Admin, Support and Read-Only users.

    Use for authorized read-only analytics and reporting
    endpoints.
    """

    message = "An authorized application role is required."

    def has_permission(self, request, view):
        return user_has_any_role(
            request.user,
            APPLICATION_ROLE_NAMES,
        )


# =========================================================
# ADMIN CARD MANAGEMENT
# =========================================================

class AdminCardManagementPermission(BasePermission):
    """
    GET / HEAD / OPTIONS:
        Admin, Support and Read-Only may view cards.

    PATCH with is_active only:
        Admin and Support may block/unblock cards.

    PATCH containing credit_limit:
        Admin only.

    Other write operations:
        Admin only.
    """

    message = (
        "Insufficient permission for this card-management operation."
    )

    def has_permission(self, request, view):

        if (
            not request.user
            or not request.user.is_authenticated
        ):
            return False

        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return user_has_any_role(
                request.user,
                APPLICATION_ROLE_NAMES,
            )

        if request.method == "PATCH":
            request_data = getattr(request, "data", {})

            # Credit-limit changes require Admin.
            # Submitting both fields also requires Admin.
            if "credit_limit" in request_data:
                return user_has_any_role(
                    request.user,
                    {ROLE_ADMIN},
                )

            # Only an is_active update may be performed
            # by Admin or Support.
            if (
                "is_active" in request_data
                and set(request_data.keys()) == {"is_active"}
            ):
                return user_has_any_role(
                    request.user,
                    {
                        ROLE_ADMIN,
                        ROLE_SUPPORT,
                    },
                )

        return user_has_any_role(
            request.user,
            {ROLE_ADMIN},
        )
