import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates default user if it doesn't exist"

    def add_arguments(self, parser):
        parser.add_argument("--password", help="User's password")

    def handle(self, *args, **options):
        user = get_user_model()
        username = "utmcraft"
        password = options.get("password") or os.getenv("DJANGO_USER_PASSWORD")
        if not user.objects.filter(username=username).exists():
            user.objects.create_user(username=username, email="", password=password)
            print(f'User "{username}" created')
