
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Use Django's secure password creation and require email.
    """

    class Meta:
        model = User
        fields = ("username", "email")


class CustomUserChangeForm(UserChangeForm):
    """
    Use Django's standard user editing form.
    """

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = User

    list_display = (
        "id",
        "username",
        "email",
        "display_roles",
        "is_staff",
        "is_active",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "groups",
    )

    ordering = ("username",)

    readonly_fields = (
        "last_login",
        "date_joined",
    )

    fieldsets = (
        (None, {
            "fields": ("username", "password"),
        }),
        ("Personal Information", {
            "fields": ("first_name", "last_name", "email"),
        }),
        ("Permissions and Roles", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )

    @admin.display(description="Roles")
    def display_roles(self, obj):
        roles = obj.groups.values_list("name", flat=True)
        return ", ".join(roles) or "No role assigned"
