from django.shortcuts import render

from .models import StudioService, StudioServiceCategory


def studio_home_view(request):
    categories = (
        StudioServiceCategory.objects.active()
        .prefetch_related("services")
        .order_by("sort_order", "name")
    )

    services = (
        StudioService.objects.active()
        .select_related("category")
        .order_by("display_order", "name")
    )

    return render(
        request,
        "studio/studio_home.html",
        {
            "categories": categories,
            "services": services,
        },
    )