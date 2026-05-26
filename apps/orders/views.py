from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from apps.events.models import Event, TicketType
from apps.merch.models import MerchItem

from .audit import record_order_created
from .forms import PublicOrderForm, PaymentProofForm
from .models import Order, OrderItem
from .services import (
    send_order_admin_notification,
    send_order_customer_confirmation,
)


def create_merch_order_view(request, slug):
    item = get_object_or_404(
        MerchItem,
        slug=slug,
        is_active=True,
    )

    if item.price_amount <= 0:
        messages.error(
            request,
            "This item is not available for online ordering yet.",
        )
        return redirect("merch:merch_detail", slug=item.slug)

    if request.method == "POST":
        form = PublicOrderForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data["quantity"]

            if item.track_stock and quantity > item.stock_quantity:
                form.add_error(
                    "quantity",
                    f"Only {item.stock_quantity} item(s) available.",
                )
            else:
                with transaction.atomic():
                    order = Order.objects.create(
                        customer_name=form.cleaned_data["customer_name"],
                        customer_email=form.cleaned_data["customer_email"],
                        customer_phone=form.cleaned_data["customer_phone"],
                        status=Order.Status.PENDING_PAYMENT,
                        currency=item.currency,
                    )

                    OrderItem.objects.create(
                        order=order,
                        merch_item=item,
                        description=item.name,
                        quantity=quantity,
                        unit_amount=item.price_amount,
                        total_amount=0,
                    )

                    order.recalculate_totals(save=True)
                    record_order_created(order, source="public_merch_order")

                send_order_admin_notification(order, request=request)
                send_order_customer_confirmation(order)

                request.session["last_order_reference"] = order.reference_code

                return redirect(
                    "orders:order_success",
                    reference_code=order.reference_code,
                )
    else:
        form = PublicOrderForm()

    return render(
        request,
        "orders/order_create.html",
        {
            "form": form,
            "order_type": "merch",
            "title": f"Order {item.name}",
            "item_name": item.name,
            "unit_price": item.price_amount,
            "currency": item.currency,
            "back_url": item.get_absolute_url()
            if hasattr(item, "get_absolute_url")
            else None,
        },
    )


def create_ticket_order_view(request, ticket_type_id):
    ticket_type = get_object_or_404(
        TicketType.objects.select_related("event"),
        pk=ticket_type_id,
        is_active=True,
        event__status=Event.Status.PUBLISHED,
        quantity_sold__lt=F("quantity_total"),
    )

    if request.method == "POST":
        form = PublicOrderForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data["quantity"]

            if quantity > ticket_type.quantity_available:
                form.add_error(
                    "quantity",
                    f"Only {ticket_type.quantity_available} ticket(s) available.",
                )
            else:
                with transaction.atomic():
                    order = Order.objects.create(
                        customer_name=form.cleaned_data["customer_name"],
                        customer_email=form.cleaned_data["customer_email"],
                        customer_phone=form.cleaned_data["customer_phone"],
                        status=Order.Status.PENDING_PAYMENT,
                        currency=ticket_type.currency,
                    )

                    OrderItem.objects.create(
                        order=order,
                        ticket_type=ticket_type,
                        description=f"{ticket_type.event.title} - {ticket_type.name}",
                        quantity=quantity,
                        unit_amount=ticket_type.price_amount,
                        total_amount=0,
                    )

                    order.recalculate_totals(save=True)
                    record_order_created(order, source="public_ticket_order")

                send_order_admin_notification(order, request=request)
                send_order_customer_confirmation(order)

                request.session["last_order_reference"] = order.reference_code

                return redirect(
                    "orders:order_success",
                    reference_code=order.reference_code,
                )
    else:
        form = PublicOrderForm()

    return render(
        request,
        "orders/order_create.html",
        {
            "form": form,
            "order_type": "ticket",
            "title": f"Order {ticket_type.name} Ticket",
            "item_name": f"{ticket_type.event.title} - {ticket_type.name}",
            "unit_price": ticket_type.price_amount,
            "currency": ticket_type.currency,
            "back_url": None,
        },
    )


def order_success_view(request, reference_code):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        reference_code=reference_code,
    )

    # Check if a payment proof already exists
    payment_proof = getattr(order, 'payment_proof', None)

    if request.method == "POST":
        # Handle payment proof upload
        form = PaymentProofForm(request.POST, request.FILES)

        if form.is_valid():
            # If a proof already exists, update it; otherwise create new
            if payment_proof:
                payment_proof_obj = form.save(commit=False)
                payment_proof_obj.order = order
                payment_proof_obj.save()
            else:
                payment_proof_obj = form.save(commit=False)
                payment_proof_obj.order = order
                payment_proof_obj.save()

            messages.success(
                request,
                "Thank you! Your payment proof has been uploaded and will be reviewed shortly.",
            )
            # Refresh the proof after save
            payment_proof = payment_proof_obj
        else:
            messages.error(
                request,
                "There was an error uploading your payment proof. Please try again.",
            )
    else:
        form = PaymentProofForm()

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
            "payment_proof": payment_proof,
            "form": form,
        },
    )