from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom application user.

    Django handles password hashing automatically.
    """

    email = models.EmailField(
        unique=True
    )

    def __str__(self):
        return self.username