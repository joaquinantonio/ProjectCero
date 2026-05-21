from apps.events.models import Artist, Event, EventArtist, EventCategory
from apps.pages.models import PageSection, SiteSettings
from apps.studio.models import StudioService, StudioServiceCategory
from apps.bookings.models import BookingRequest

print(Artist._meta.db_table)
print(Event._meta.db_table)
print(EventArtist._meta.db_table)
print(EventCategory._meta.db_table)
print(PageSection._meta.db_table)
print(SiteSettings._meta.db_table)
print(StudioService._meta.db_table)
print(StudioServiceCategory._meta.db_table)
print(BookingRequest._meta.db_table)