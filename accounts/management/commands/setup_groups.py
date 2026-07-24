from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from accounts.models import User


class Command(BaseCommand):
    help = "Create default Groups matching each role"

    def handle(self, *args, **kwargs):
        role_names = [choice[1] for choice in User.Role.choices]

        for name in role_names:
            group, created = Group.objects.get_or_create(name=name)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"{status}: {name}")

        self.stdout.write(self.style.SUCCESS("Groups setup complete."))