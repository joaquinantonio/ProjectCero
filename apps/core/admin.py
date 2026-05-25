from django.contrib import admin
from django.utils.html import escape, format_html, mark_safe

def make_bulk_update_action(*, action_name, field_name, value, description, success_message):
    @admin.action(description=description)
    def action(modeladmin, request, queryset):
        updated = queryset.update(**{field_name: value})
        modeladmin.message_user(request, success_message.format(updated=updated))

    action.__name__ = action_name
    return action


def basic_fieldset(obj, base_fields, *, slug_field="slug", new_description=None, existing_description=None):
    """Return a 'Basic' fieldset tuple, including the slug and a different description when editing.

    - obj: the model instance (or None) — if truthy, include slug_field in the fields and use existing_description.
    - base_fields: iterable of base field names (for create view)
    - slug_field: name of the slug field to include when editing
    - new_description: description for the create view
    - existing_description: description for the change view
    """
    base = tuple(base_fields)
    if obj:
        fields = tuple(list(base) + [slug_field])
        description = existing_description or ""
    else:
        fields = base
        description = new_description or ""

    return ("Basic", {"fields": fields, "description": description})

def render_admin_badge(label, tone="neutral"):
    return format_html(
        '<span class="status-badge status-badge--{}">{}</span>',
        tone,
        label,
    )


def render_boolean_badge(
    value,
    *,
    true_label="Yes",
    false_label="No",
    true_tone="success",
    false_tone="neutral",
):
    if value:
        return render_admin_badge(true_label, true_tone)
    return render_admin_badge(false_label, false_tone)

class AdminImagePreviewMixin:
    image_preview_field = None

    @admin.display(description="Preview")
    def image_preview(self, obj):
        field_name = self.image_preview_field
        if not field_name:
            return "-"
        image_field = getattr(obj, field_name, None)
        if image_field and getattr(image_field, "url", None):
            return mark_safe(
                f'<img src="{escape(image_field.url)}" class="cero-admin-thumb" loading="lazy" />'
            )
        return "-"


class TimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25


class SuperuserDeleteOnlyAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class HideFromNonSuperusersAdminMixin:
    def get_model_perms(self, request):
        perms = admin.ModelAdmin.get_model_perms(self, request)
        if request.user.is_superuser:
            return perms
        return {}


class ReadonlyOnChangeAdminMixin:
    """Mixin that marks configured fields as readonly when editing an existing object.

    Admin classes can set `readonly_on_change = ("slug", "published_at")` to have
    those fields appended to readonly_fields for change views.
    """
    readonly_on_change = ()

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj:
            for f in self.readonly_on_change:
                if f not in base:
                    base.append(f)
        return tuple(base)

