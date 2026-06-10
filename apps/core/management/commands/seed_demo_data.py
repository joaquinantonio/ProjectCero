# Sample data courtest of AI
# usage: python manage.py seed_demo_data
# reset: python manage.py seed_demo_data --reset
from datetime import timedelta
from typing import Dict, Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.artists.models import Artist
from apps.bookings.models import BookingRequest
from apps.events.models import Event, EventArtist, EventCategory
from apps.pages.models import PageSection, SiteSettings
from apps.studio.models import StudioService, StudioServiceCategory


class Command(BaseCommand):
    help = "Seed demo data for local development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo content before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options["reset"]

        if reset:
            self.stdout.write(self.style.WARNING("Resetting demo data..."))
            # Clear in a short, explicit list to keep order understandable
            for model in [
                EventArtist,
                Event,
                EventCategory,
                Artist,
                StudioService,
                StudioServiceCategory,
                PageSection,
                SiteSettings,
                BookingRequest,
            ]:
                model.objects.all().delete()

        self.seed_site_settings()
        self.seed_page_sections()
        categories = self.seed_event_categories()
        artists = self.seed_artists()
        self.seed_events(categories, artists)
        studio_categories = self.seed_studio_categories()
        self.seed_studio_services(studio_categories)
        self.seed_booking_requests()

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def seed_site_settings(self):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                "site_name": "CeroPJ",
                "tagline": "Life is good when you're here.",
                "contact_email": "hello@ceropj.com",
                "contact_phone": "+60 12-345 6789",
                "address_text": (
                    "G-3-6, Parklane Commercial Park, \n Jalan SS 7/26,\n 47301 Petaling Jaya,\nSelangor, Malaysia"
                ),
                "google_maps_url": "https://maps.app.goo.gl/ecvTbmWd73Du318n9",
                "instagram_url": "https://instagram.com/ceropj",
                "facebook_url": "https://facebook.com/ceropj",
                "tiktok_url": "https://tiktok.com/@ceropj",
                "youtube_url": "https://youtube.com/@ceropj",
                "whatsapp_url": "https://wa.me/60123456789",
            },
        )

    def seed_page_sections(self):
        sections = [
            {
                "page_key": "home",
                "section_key": "creative-space",
                "title": "A space built for musicians",
                "subtitle": "Recording, rehearsals, and live performances",
                "body": (
                    "CeroPJ is designed for artists who want a flexible creative space.\n"
                    "Use it for recording sessions, intimate live nights, collaborations, and rehearsals."
                ),
                "sort_order": 1,
                "is_active": True,
            },
            {
                "page_key": "home",
                "section_key": "community",
                "title": "A community",
                "subtitle": "A venue for artists and audiences",
                "body": (
                    "We support emerging musicians, featured bands, and special live showcases.\n"
                    "The venue is designed to create a close connection between performers and audiences."
                ),
                "sort_order": 2,
                "is_active": True,
            },
            {
                "page_key": "home",
                "section_key": "bookings",
                "title": "Studio sessions and event enquiries",
                "subtitle": "Work with the space in different ways",
                "body": (
                    "Looking for studio time, a rehearsal slot, or a venue enquiry?\n"
                    "Send a booking request and we’ll get back to you."
                ),
                "sort_order": 3,
                "is_active": True,
            },
            {
                "page_key": "about",
                "section_key": "about-main",
                "title": "About the venue",
                "subtitle": "A place for creative work and live music",
                "body": (
                    "CeroPJ brings together recording, collaboration, and intimate performances.\n"
                    "It is built for artists who want both a working studio and a live audience connection."
                ),
                "sort_order": 1,
                "is_active": True,
            },
            {
                "page_key": "contact",
                "section_key": "contact-main",
                "title": "Let’s talk",
                "subtitle": "Studio sessions, collaborations, and venue enquiries",
                "body": (
                    "Use the booking options to send us your request.\n"
                    "We welcome enquiries from artists, promoters, and collaborators."
                ),
                "sort_order": 1,
                "is_active": True,
            },
        ]

        for section in sections:
            PageSection.objects.update_or_create(
                page_key=section["page_key"],
                section_key=section["section_key"],
                defaults=section,
            )

    def _upsert_map(self, model, lookup_field: str, rows: Iterable[dict], map_key_field: str) -> Dict[str, object]:
        mapping: Dict[str, object] = {}
        for row in rows:
            lookup_value = row[lookup_field]
            defaults = {k: v for k, v in row.items() if k != lookup_field}
            obj, _ = model.objects.update_or_create(**{lookup_field: lookup_value}, defaults=defaults)
            mapping[row[map_key_field]] = obj
        return mapping

    def seed_event_categories(self):
        rows = [
            {"name": "Live Gig", "slug": "live-gig", "sort_order": 1, "is_active": True},
            {"name": "Open Mic", "slug": "open-mic", "sort_order": 2, "is_active": True},
            {"name": "Jam Session", "slug": "jam-session", "sort_order": 3, "is_active": True},
            {"name": "Special Showcase", "slug": "special-showcase", "sort_order": 4, "is_active": True},
        ]
        return self._upsert_map(EventCategory, "slug", rows, "slug")

    def seed_artists(self):
        rows = [
            {
                "name": "Midnight Generation",
                "slug": "midnight-generation",
                "artist_type": Artist.ArtistType.BAND,
                "is_featured": True,
                "feature_order": 1,
                "short_bio": "Disco-electronic-pop band from Chihuahua",
                "bio": (
                    "Midnight Generation is a Mexican disco-electronic-pop band from Chihuahua, formed in 2015."
                    "Led by vocalist and multi-instrumentalist Fernando Mares, the group blends classic disco, funk, and modern French-touch house, and has toured internationally at major festivals like Austin City Limits. "
                ),
                "is_active": True,
            },
            {
                "name": "CLUBZ",
                "slug": "clubz",
                "artist_type": Artist.ArtistType.BAND,
                "is_featured": True,
                "feature_order": 2,
                "short_bio": "A Mexican electropop and indie pop duo, formed in 2013 in Monterrey, Mexico.",
                "bio": (
                    "CLUBZ is a Mexican electropop and indie pop duo, formed in 2013 in Monterrey, Mexico. It consists of Coco Santos (vocals and keyboards) and Orlando Fernández (vocals and guitar). They won Best New Artist and Best Pop Album for their mini-album Texturas in 2015 as well as Song of the Year for \"Épocas\" in 2016 at the IMAs Awards."
                ),
                "is_active": True,
            },
            {
                "name": "Rawayana",
                "slug": "rawayana",
                "artist_type": Artist.ArtistType.BAND,
                "is_featured": True,
                "feature_order": 3,
                "short_bio": "Known for their signature \"trippy pop\" sound, they seamlessly blend reggae, funk, soul, R&B, and rock with Caribbean rhythms.",
                "bio": (
                    "Rawayana is a multiple Grammy-winning Venezuelan band formed in Caracas in 2007. Known for their signature \"trippy pop\" sound, they seamlessly blend reggae, funk, soul, R&B, and rock with Caribbean rhythms. They are one of Latin America's most celebrated and innovative musical acts."
                ),
                "is_active": True,
            },
            {
                "name": "Neutro Shorty",
                "slug": "neutro-shorty",
                "artist_type": Artist.ArtistType.SOLO,
                "is_featured": True,
                "feature_order": 4,
                "short_bio": "Venezuelan rapper and singer.",
                "bio": (
                    "Hailing from Caracas, he is celebrated for blending Latin hip-hop, trap, and salsa music. Rising from the underground, he has become a leading voice for Latin American youth, racking up hundreds of millions of streams."
                ),
                "is_active": True,
            },
        ]
        return self._upsert_map(Artist, "slug", rows, "slug")

    def seed_events(self, categories, artists):
        now = timezone.now()

        rows = [
            {
                "category": categories["live-gig"],
                "title": "Friday Sessions: Midnight Generation Live",
                "slug": "friday-sessions-midnight-generation-live",
                "short_description": "A neo-soul night with groove-heavy live arrangements.",
                "description": (
                    "Join us for a Friday night session with Midnight Generation performing original songs, "
                    "reworked covers, and late-night lounge grooves in an intimate venue setup."
                ),
                "start_at": now + timedelta(days=5),
                "end_at": (now + timedelta(days=5)) + timedelta(hours=2),
                "location_text": "CeroPJ",
                "ticket_url": "https://example.com/tickets/clubz",
                "price_text": "RM35",
                "status": Event.Status.PUBLISHED,
                "is_featured": True,
                "published_at": now,
                "artists": [("midnight-generation", "Featured Band", 1)],
            },
            {
                "category": categories["open-mic"],
                "title": "Open Mic Night Vol. 6",
                "slug": "open-mic-night-vol-6",
                "short_description": "An open stage for emerging performers and community jammers.",
                "description": "A welcoming night for new acts, comedians, songwriters, and musicians who want to share a set.",
                "start_at": now + timedelta(days=10),
                "end_at": (now + timedelta(days=10)) + timedelta(hours=3),
                "location_text": "CeroPJ",
                "ticket_url": "https://example.com/tickets/open-mic-6",
                "price_text": "RM20",
                "status": Event.Status.PUBLISHED,
                "is_featured": True,
                "published_at": now,
                "artists": [("clubz", "Host DJ", 1)],
            },
            {
                "category": categories["special-showcase"],
                "title": "CLUBZ Acoustic Showcase",
                "slug": "clubz-acoustic-showcase",
                "short_description": "An intimate acoustic set from CLUBZ.",
                "description": "A singer-songwriter night featuring original material and carefully reworked covers.",
                "start_at": now + timedelta(days=14),
                "end_at": (now + timedelta(days=14)) + timedelta(hours=2),
                "location_text": "CeroPJ",
                "ticket_url": "https://example.com/tickets/clubz",
                "price_text": "RM30",
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
                "published_at": now,
                "artists": [("clubz", "Featured Artist", 1)],
            },
            {
                "category": categories["live-gig"],
                "title": "Rawayana Saturday Set",
                "slug": "rawayana-saturday-set",
                "short_description": "An upbeat funk-soul live set from Rawayana.",
                "description": "Expect a high-energy set with audience interaction and a modern live sound.",
                "start_at": now + timedelta(days=20),
                "end_at": (now + timedelta(days=20)) + timedelta(hours=2),
                "location_text": "CeroPJ",
                "ticket_url": "https://example.com/tickets/rawayana",
                "price_text": "RM40",
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
                "published_at": now,
                "artists": [("rawayana", "Featured Band", 1)],
            },
            {
                "category": categories["jam-session"],
                "title": "Community Jam Night",
                "slug": "community-jam-night",
                "short_description": "A relaxed collaborative session for musicians and regulars.",
                "description": "Bring your instrument, meet other players, and join an informal jam session.",
                "start_at": now - timedelta(days=12),
                "end_at": (now - timedelta(days=12)) + timedelta(hours=2),
                "location_text": "CeroPJ",
                "ticket_url": "",
                "price_text": "RM15",
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
                "published_at": now - timedelta(days=20),
                "artists": [("neutro-shorty", "Guest Set", 1), ("midnight-generation", "Guest Set", 2)],
            },
        ]

        for row in rows:
            artist_links = row.pop("artists")
            event, _ = Event.objects.update_or_create(slug=row["slug"], defaults=row)

            EventArtist.objects.filter(event=event).delete()
            links = [
                EventArtist(event=event, artist=artists[slug], role_name=role, sort_order=so)
                for slug, role, so in artist_links
            ]
            EventArtist.objects.bulk_create(links)

    def seed_studio_categories(self):
        rows = [
            {"name": "Recording", "slug": "recording", "sort_order": 1, "is_active": True},
            {"name": "Rehearsal", "slug": "rehearsal", "sort_order": 2, "is_active": True},
            {"name": "Mixing & Production", "slug": "mixing-production", "sort_order": 3, "is_active": True},
            {"name": "Live Session Setup", "slug": "live-session-setup", "sort_order": 4, "is_active": True},
        ]
        return self._upsert_map(StudioServiceCategory, "slug", rows, "slug")

    def seed_studio_services(self, categories):
        rows = [
            {
                "category": categories["recording"],
                "name": "Vocal Recording Session",
                "slug": "vocal-recording-session",
                "short_description": "Clean studio setup for solo vocal tracking and guided recording.",
                "description": "Ideal for singers, songwriters, and artists who need a focused session for vocals, demos, or polished single tracking.",
                "price_text": "From RM120 / session",
                "duration_text": "2 hours",
                "is_featured": True,
                "is_active": True,
                "display_order": 1,
            },
            {
                "category": categories["rehearsal"],
                "name": "Band Rehearsal Block",
                "slug": "band-rehearsal-block",
                "short_description": "Dedicated rehearsal slot for bands and collaborative sets.",
                "description": "A flexible rehearsal block for live prep, arrangements, and practice.",
                "price_text": "From RM90 / block",
                "duration_text": "3 hours",
                "is_featured": True,
                "is_active": True,
                "display_order": 2,
            },
            {
                "category": categories["live-session-setup"],
                "name": "Live Session Recording",
                "slug": "live-session-recording",
                "short_description": "Capture intimate live performances with a controlled setup.",
                "description": "Suitable for stripped-down performances, live videos, and special sessions.",
                "price_text": "Custom quote",
                "duration_text": "Based on session",
                "is_featured": True,
                "is_active": True,
                "display_order": 3,
            },
            {
                "category": categories["mixing-production"],
                "name": "Mixing Consultation",
                "slug": "mixing-consultation",
                "short_description": "Review your session and discuss the next production steps.",
                "description": "A focused consultation for mix direction, arrangement feedback, and workflow.",
                "price_text": "From RM150",
                "duration_text": "1.5 hours",
                "is_featured": False,
                "is_active": True,
                "display_order": 4,
            },
        ]

        for row in rows:
            StudioService.objects.update_or_create(slug=row["slug"], defaults=row)

    def seed_booking_requests(self):
        rows = [
            {
                "reference_code": "BK-DEMO-00001",
                "request_type": BookingRequest.RequestType.STUDIO,
                "name": "Miyashita Rena",
                "email": "rena@example.com",
                "phone": "+60 12-111 2222",
                "preferred_date": timezone.localdate() + timedelta(days=7),
                "message": "Looking for a recording session for a solo vocal track.",
                "status": BookingRequest.Status.NEW,
            },
            {
                "reference_code": "BK-DEMO-00002",
                "request_type": BookingRequest.RequestType.VENUE,
                "name": "George Michael",
                "email": "george@example.com",
                "phone": "+60 12-333 4444",
                "preferred_date": timezone.localdate() + timedelta(days=21),
                "guest_count": 60,
                "message": "Interested in discussing a private event at the venue.",
                "status": BookingRequest.Status.IN_REVIEW,
            },
        ]

        for row in rows:
            BookingRequest.objects.update_or_create(reference_code=row["reference_code"], defaults=row)
