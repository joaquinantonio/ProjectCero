from django.core.paginator import Paginator
from django.utils.text import slugify


def paginate_queryset(request, queryset, per_page=9):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def generate_unique_slug(instance, source_value: str, slug_field: str = "slug", max_length: int = 170) -> str:
    base_slug = slugify(source_value or "")[:max_length].strip("-")
    if not base_slug:
        base_slug = "item"

    model_class = instance.__class__
    slug = base_slug
    counter = 2

    while model_class.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        suffix = f"-{counter}"
        trimmed = base_slug[: max_length - len(suffix)].rstrip("-")
        slug = f"{trimmed}{suffix}"
        counter += 1

    return slug


def apply_limit(queryset, limit):
    """Return a sliced queryset if limit is provided, otherwise return the full queryset.

    This helper reduces repeated `if limit: return qs[:limit]` patterns in selectors.
    """
    return queryset[:limit] if limit else queryset
