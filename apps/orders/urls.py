from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path(
        "merch/<slug:slug>/",
        views.create_merch_order_view,
        name="create_merch_order",
    ),
    path(
        "tickets/<int:ticket_type_id>/",
        views.create_ticket_order_view,
        name="create_ticket_order",
    ),
    path(
        "success/<str:reference_code>/",
        views.order_success_view,
        name="order_success",
    ),
]