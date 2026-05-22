from django.contrib import admin

from apps.core.admin import SuperuserDeleteOnlyAdminMixin, TimestampedAdmin
from .models import EnquirySubmission


@admin.action(description="Mark selected enquiries as In Review")
def mark_in_review(modeladmin, request, queryset):
    updated = queryset.update(status=EnquirySubmission.Status.IN_REVIEW)
    modeladmin.message_user(request, f"{updated} enquiry(ies) marked as In Review.")


@admin.action(description="Mark selected enquiries as Replied")
def mark_replied(modeladmin, request, queryset):
    updated = queryset.update(status=EnquirySubmission.Status.REPLIED)
    modeladmin.message_user(request, f"{updated} enquiry(ies) marked as Replied.")


@admin.action(description="Mark selected enquiries as Closed")
def mark_closed(modeladmin, request, queryset):
    updated = queryset.update(status=EnquirySubmission.Status.CLOSED)
    modeladmin.message_user(request, f"{updated} enquiry(ies) marked as Closed.")


@admin.register(EnquirySubmission)
class EnquirySubmissionAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "reference_code",
        "enquiry_type",
        "name",
        "email",
        "status",
        "created_at",
    )
    list_filter = ("enquiry_type", "status", "created_at")
    search_fields = (
        "reference_code",
        "name",
        "email",
        "phone",
        "subject",
        "message",
        "admin_notes",
    )
    search_help_text = "Search by reference, name, email, phone, subject, message, or admin notes"
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = [mark_in_review, mark_replied, mark_closed]
    autocomplete_fields = ("related_event", "related_merch")
    list_select_related = ("related_event", "related_merch")

    fieldsets = (
        ("Submission", {
            "fields": ("reference_code", "enquiry_type", "status"),
        }),
        ("Sender", {
            "fields": ("name", "email", "phone"),
        }),
        ("Details", {
            "fields": ("subject", "preferred_date", "related_event", "related_merch", "amount_text", "message"),
        }),
        ("Internal Notes", {
            "fields": ("admin_notes",),
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    readonly_fields = ("reference_code", "created_at", "updated_at")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.extend([
                "enquiry_type",
                "name",
                "email",
                "phone",
                "subject",
                "preferred_date",
                "amount_text",
                "message",
            ])
        return tuple(readonly)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "related_event" in form.base_fields:
            form.base_fields["related_event"].label = "Related event"
            form.base_fields["related_event"].help_text = "Optional. You can link the enquiry to a specific event."

        if "related_merch" in form.base_fields:
            form.base_fields["related_merch"].label = "Related merch item"
            form.base_fields["related_merch"].help_text = "Optional. You can link the enquiry to a merch item."

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].label = "Internal notes"
            form.base_fields["admin_notes"].help_text = "Visible only in admin."

        return form