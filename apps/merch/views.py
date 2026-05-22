from django.views.generic import DetailView, ListView

from .models import MerchItem


class MerchListView(ListView):
    model = MerchItem
    template_name = "merch/merch_list.html"
    context_object_name = "items"
    paginate_by = 12

    def get_featured_items(self):
        return (
            MerchItem.objects.filter(is_active=True, is_featured=True)
            .order_by("display_order", "name")[:3]
        )

    def get_queryset(self):
        return MerchItem.objects.filter(is_active=True).order_by("display_order", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_items"] = self.get_featured_items()
        return context


class MerchDetailView(DetailView):
    model = MerchItem
    template_name = "merch/merch_detail.html"
    context_object_name = "item"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return MerchItem.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_items"] = (
            MerchItem.objects.filter(is_active=True)
            .exclude(pk=self.object.pk)
            .order_by("display_order", "name")[:3]
        )
        return context