from django.shortcuts import render

from .models import StudioService


def studio_home_view(request):
    services = (
        StudioService.objects.active()
        .order_by("display_order", "name")
    )

    return render(
        request,
        "studio/studio_home.html",
        {
            "services": services,
        },
    )