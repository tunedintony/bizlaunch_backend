from decouple import config
from django.core.management.base import BaseCommand

from bizlaunch.users.models import User


class Command(BaseCommand):
    help = "Create a superuser if it doesn't already exist"

    def handle(self, *args, **kwargs):
        # Fetch admin email and password from environment variables
        admin_email = config("DJANGO_ADMIN_EMAIL", default="admin@example.com")
        admin_password = config("DJANGO_ADMIN_PASSWORD", default="adminpassword")

        # Check if a superuser with the given email already exists
        if not User.objects.filter(email=admin_email).exists():
            # Create the superuser
            User.objects.create_superuser(email=admin_email, password=admin_password)
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{admin_email}' created successfully.")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Superuser '{admin_email}' already exists.")
            )
