from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


GROUP_DEFINITIONS = {
    "Editor": [
        "view_newspost",
        "add_newspost",
        "change_newspost",
        "view_merchitem",
        "add_merchitem",
        "change_merchitem",
        "view_enquirysubmission",
        "change_enquirysubmission",

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
        "view_booking",
        "add_booking",
        "change_booking",
        "view_bookingresource",
    ],

    "Website Manager": [
        "view_newspost",
        "add_newspost",
        "change_newspost",
        "view_merchitem",
        "add_merchitem",
        "change_merchitem",

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
        "view_booking",
        "add_booking",
        "change_booking",
        "view_bookingresource",
    ],

    "Bookings Operator": [
        # Booking requests / intake
        "view_bookingrequest",
        "change_bookingrequest",

        # Calendar bookings / actual blocking records
        "view_booking",
        "add_booking",
        "change_booking",
        "view_bookingresource",

        # Enquiries
        "view_enquirysubmission",
        "change_enquirysubmission",

        # Optional context visibility
        "view_event",
        "view_artist",
    ],

    "Read Only": [
        "view_newspost",
        "view_merchitem",
        "view_enquirysubmission",
        "view_bookingrequest",
        "view_booking",
        "view_bookingresource",

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
            permission_codenames = list(dict.fromkeys(permission_codenames))
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