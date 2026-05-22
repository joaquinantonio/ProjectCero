from django.contrib import admin
from django.utils import timezone

from apps.core.admin import AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin
from .models import NewsPost


@admin.action(description="Mark selected posts as Published")
def make_published(modeladmin, request, queryset):
    updated = 0
    for post in queryset:
        if post.status != NewsPost.Status.PUBLISHED:
            post.status = NewsPost.Status.PUBLISHED
            if not post.published_at:
                post.published_at = timezone.now()
            post.save(update_fields={"status", "published_at"})
            updated += 1
    modeladmin.message_user(request, f"{updated} post(s) marked as Published.")


@admin.action(description="Mark selected posts as Draft")
def make_draft(modeladmin, request, queryset):
    updated = queryset.update(status=NewsPost.Status.DRAFT)
    modeladmin.message_user(request, f"{updated} post(s) marked as Draft.")


@admin.action(description="Feature selected posts")
def make_featured(modeladmin, request, queryset):
    updated = queryset.update(is_featured=True)
    modeladmin.message_user(request, f"{updated} post(s) marked as Featured.")


@admin.action(description="Unfeature selected posts")
def make_unfeatured(modeladmin, request, queryset):
    updated = queryset.update(is_featured=False)
    modeladmin.message_user(request, f"{updated} post(s) unfeatured.")


@admin.register(NewsPost)
class NewsPostAdmin(AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    image_preview_field = "cover_image"

    list_display = (
        "title",
        "status",
        "is_featured",
        "image_preview",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "is_featured", "published_at")
    search_fields = ("title", "summary", "body")
    search_help_text = "Search by title, summary, or body"
    ordering = ("-published_at", "-created_at", "title")
    actions = [make_published, make_draft, make_featured, make_unfeatured]
    date_hierarchy = "published_at"

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                ("Basic", {
                    "fields": ("title", "slug", "status", "is_featured"),
                    "description": "The slug was generated automatically when this post was created. It is now locked to keep news links stable.",
                }),
                ("Content", {
                    "fields": ("summary", "body", "cover_image"),
                }),
                ("Publishing", {
                    "fields": ("published_at",),
                }),
                ("System", {
                    "fields": ("created_at", "updated_at"),
                }),
            )

        return (
            ("Basic", {
                "fields": ("title", "status", "is_featured"),
                "description": "The slug will be generated automatically from the title when this post is first created.",
            }),
            ("Content", {
                "fields": ("summary", "body", "cover_image"),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.extend(["slug", "published_at"])
        return tuple(readonly)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "summary" in form.base_fields:
            form.base_fields["summary"].label = "Short summary"
            form.base_fields["summary"].help_text = "Used on cards, previews, and metadata."

        if "body" in form.base_fields:
            form.base_fields["body"].help_text = "Main public content for the news post."

        return form