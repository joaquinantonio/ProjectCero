from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


GROUP_DEFINITIONS = {
    "Editor": [
        # Pages
        "view_sitesettings",
        "change_sitesettings",
        "view_pagesection",
        "add_pagesection",
        "change_pagesection",

        # Artists
        "view_artist",
        "add_artist",
        "change_artist",

        # Events
        "view_event",
        "add_event",
        "change_event",
        "view_eventcategory",
        "add_eventcategory",
        "change_eventcategory",

        # Studio
        "view_studioservice",
        "add_studioservice",
        "change_studioservice",
        "view_studioservicecategory",
        "add_studioservicecategory",
        "change_studioservicecategory",

        # Bookings
        "view_bookingrequest",
        "change_bookingrequest",
    ],

    "Website Manager": [
        # Pages
        "view_sitesettings",
        "change_sitesettings",
        "view_pagesection",
        "add_pagesection",
        "change_pagesection",

        # Artists
        "view_artist",
        "add_artist",
        "change_artist",

        # Studio
        "view_studioservice",
        "add_studioservice",
        "change_studioservice",
        "view_studioservicecategory",
        "add_studioservicecategory",
        "change_studioservicecategory",
    ],

    "Events Manager": [
        # Events
        "view_event",
        "add_event",
        "change_event",
        "view_eventcategory",
        "add_eventcategory",
        "change_eventcategory",

        # Artists
        "view_artist",
        "add_artist",
        "change_artist",

        # Bookings
        "view_bookingrequest",
        "change_bookingrequest",
    ],

    "Bookings Operator": [
        # Bookings only
        "view_bookingrequest",
        "change_bookingrequest",

        # Optional context visibility
        "view_event",
        "view_artist",
    ],

    "Read Only": [
        # Pages
        "view_sitesettings",
        "view_pagesection",

        # Artists
        "view_artist",

        # Events
        "view_event",
        "view_eventcategory",

        # Studio
        "view_studioservice",
        "view_studioservicecategory",

        # Bookings
        "view_bookingrequest",
    ],
}


class Command(BaseCommand):
    help = "Create or update default user groups and permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing permissions on managed groups before reapplying defaults.",
        )

    def handle(self, *args, **options):
        clear = options["clear"]

        for group_name, permission_codenames in GROUP_DEFINITIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if clear:
                group.permissions.clear()

            permissions = Permission.objects.filter(codename__in=permission_codenames)
            found_codenames = set(permissions.values_list("codename", flat=True))
            missing_codenames = sorted(set(permission_codenames) - found_codenames)

            group.permissions.set(permissions)
            group.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {group_name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated group: {group_name}"))

            self.stdout.write(f"  Assigned {permissions.count()} permissions")

            if missing_codenames:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Missing permissions for {group_name}: {', '.join(missing_codenames)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Default groups setup complete."))