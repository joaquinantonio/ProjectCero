from django.contrib import admin

from apps.core.admin import (
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    make_bulk_update_action,
    render_admin_badge,
)
from .models import EnquirySubmission


mark_in_review = make_bulk_update_action(
    action_name="mark_in_review",
    field_name="status",
    value=EnquirySubmission.Status.IN_REVIEW,
    description="Mark selected enquiries as In Review",
    success_message="{updated} enquiry(ies) marked as In Review.",
)

mark_replied = make_bulk_update_action(
    action_name="mark_replied",
    field_name="status",
    value=EnquirySubmission.Status.REPLIED,
    description="Mark selected enquiries as Replied",
    success_message="{updated} enquiry(ies) marked as Replied.",
)

mark_closed = make_bulk_update_action(
    action_name="mark_closed",
    field_name="status",
    value=EnquirySubmission.Status.CLOSED,
    description="Mark selected enquiries as Closed",
    success_message="{updated} enquiry(ies) marked as Closed.",
)


@admin.register(EnquirySubmission)
class EnquirySubmissionAdmin(
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
):
    list_display = (
        "reference_code",
        "enquiry_type_badge",
        "name",
        "email",
        "status_badge",
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

    readonly_fields = ("reference_code", "created_at", "updated_at")
    readonly_on_change = (
        "enquiry_type",
        "name",
        "email",
        "phone",
        "subject",
        "preferred_date",
        "amount_text",
        "message",
    )

    def has_add_permission(self, request):
        return request.user.is_superuser

    @admin.display(ordering="enquiry_type", description="Type")
    def enquiry_type_badge(self, obj):
        tone_map = {
            EnquirySubmission.EnquiryType.GENERAL: "neutral",
            EnquirySubmission.EnquiryType.MERCH: "accent",
            EnquirySubmission.EnquiryType.PAYMENT: "info",
        }
        return render_admin_badge(
            obj.get_enquiry_type_display(),
            tone_map.get(obj.enquiry_type, "neutral"),
        )

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            EnquirySubmission.Status.NEW: "warning",
            EnquirySubmission.Status.IN_REVIEW: "info",
            EnquirySubmission.Status.REPLIED: "success",
            EnquirySubmission.Status.CLOSED: "neutral",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    def get_fieldsets(self, request, obj=None):
        workflow_fields = ("status", "admin_notes")
        if obj:
            workflow_fields = ("reference_code", "status", "admin_notes")

        return (
            (
                "Workflow",
                {
                    "fields": workflow_fields,
                    "classes": ("wide", "workflow-panel"),
                    "description": "Update the status and internal notes here. The original submission details are shown below.",
                },
            ),
            (
                "Sender",
                {
                    "fields": (("name", "email"), "phone"),
                },
            ),
            (
                "Enquiry Details",
                {
                    "fields": (
                        "enquiry_type",
                        "subject",
                        ("related_event", "related_merch"),
                        ("preferred_date", "amount_text"),
                    ),
                    "description": "Submitted enquiry details. Related event or merch item can be linked internally if needed.",
                },
            ),
            (
                "Submitted Message",
                {
                    "fields": ("message",),
                },
            ),
            (
                "System",
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "status" in form.base_fields:
            form.base_fields["status"].help_text = "Use this to track the enquiry as it moves through your workflow."

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].label = "Internal notes"
            form.base_fields["admin_notes"].help_text = "Visible only in admin."
            form.base_fields["admin_notes"].widget.attrs["rows"] = 8

        if "related_event" in form.base_fields:
            form.base_fields["related_event"].label = "Related event"
            form.base_fields["related_event"].help_text = "Optional."

        if "related_merch" in form.base_fields:
            form.base_fields["related_merch"].label = "Related merch item"
            form.base_fields["related_merch"].help_text = "Optional."

        if "amount_text" in form.base_fields:
            form.base_fields["amount_text"].label = "Amount / package"

        if "message" in form.base_fields:
            form.base_fields["message"].label = "Submitted message"
            form.base_fields["message"].widget.attrs["rows"] = 6

        return form