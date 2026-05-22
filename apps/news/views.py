from django.views.generic import DetailView, ListView

from .models import NewsPost


class NewsListView(ListView):
    model = NewsPost
    template_name = "news/news_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_featured_post(self):
        return (
            NewsPost.objects.filter(
                status=NewsPost.Status.PUBLISHED,
                is_featured=True,
            )
            .order_by("-published_at", "-created_at")
            .first()
        )

    def get_queryset(self):
        queryset = (
            NewsPost.objects.filter(status=NewsPost.Status.PUBLISHED)
            .order_by("-published_at", "-created_at")
        )

        featured_post = self.get_featured_post()
        if featured_post:
            queryset = queryset.exclude(pk=featured_post.pk)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_post"] = self.get_featured_post()
        return context


class NewsDetailView(DetailView):
    model = NewsPost
    template_name = "news/news_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return NewsPost.objects.filter(status=NewsPost.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_posts"] = (
            NewsPost.objects.filter(status=NewsPost.Status.PUBLISHED)
            .exclude(pk=self.object.pk)
            .order_by("-published_at", "-created_at")[:3]
        )
        return context