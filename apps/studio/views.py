from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from apps.core.utils import paginate_queryset
from .models import StudioService, Equipment


def studio_home_view(request):
    services = StudioService.objects.active().order_by("display_order", "name")
    search_query = request.GET.get("q", "").strip()

    if search_query:
        services = services.filter(
            Q(name__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    page_obj = paginate_queryset(request, services, per_page=8)

    return render(
        request,
        "studio/studio_home.html",
        {
            "services": page_obj,
            "search_query": search_query,
        },
    )


def studio_service_detail_view(request, slug):
    try:
        service = StudioService.objects.active().get(slug=slug)
    except StudioService.DoesNotExist:
        raise Http404("Studio service not found")

    return render(
        request,
        "studio/studio_service_detail.html",
        {
            "service": service,
        },
    )


def equipment_list_view(request):
    equipment = Equipment.objects.filter(is_active=True).order_by("name")
    search_query = request.GET.get("q", "").strip()

    if search_query:
        equipment = equipment.filter(
            Q(name__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    page_obj = paginate_queryset(request, equipment, per_page=16)

    return render(
        request,
        "studio/equipment_list.html",
        {
            "equipment": page_obj,
            "search_query": search_query,
        },
    )
