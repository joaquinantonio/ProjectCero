from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.events.models import TicketType
from apps.merch.models import MerchItem

from .audit import record_inventory_committed, record_inventory_released


def validate_order_inventory(order):
    errors = []

    items = order.items.select_related(
        "merch_item",
        "ticket_type",
        "ticket_type__event",
    )

    for item in items:
        if item.merch_item_id:
            merch_item = item.merch_item

            if merch_item.track_stock and item.quantity > merch_item.stock_quantity:
                errors.append(
                    f"{merch_item.name}: only {merch_item.stock_quantity} item(s) available."
                )

        elif item.ticket_type_id:
            ticket_type = item.ticket_type

            if item.quantity > ticket_type.quantity_available:
                errors.append(
                    f"{ticket_type.event.title} - {ticket_type.name}: "
                    f"only {ticket_type.quantity_available} ticket(s) available."
                )

    if errors:
        raise ValidationError(errors)


@transaction.atomic
def commit_order_inventory(order, created_by=None, source="system"):
    order = order.__class__.objects.select_for_update().get(pk=order.pk)

    if order.inventory_committed_at:
        return False

    items = list(
        order.items.select_related(
            "merch_item",
            "ticket_type",
            "ticket_type__event",
        )
    )

    for item in items:
        if item.merch_item_id:
            merch_item = MerchItem.objects.select_for_update().get(pk=item.merch_item_id)

            if merch_item.track_stock:
                if item.quantity > merch_item.stock_quantity:
                    raise ValidationError(
                        f"{merch_item.name}: only {merch_item.stock_quantity} item(s) available."
                    )

                merch_item.stock_quantity = F("stock_quantity") - item.quantity
                merch_item.save(update_fields=["stock_quantity", "updated_at"])

        elif item.ticket_type_id:
            ticket_type = TicketType.objects.select_for_update().get(pk=item.ticket_type_id)

            available = ticket_type.quantity_total - ticket_type.quantity_sold

            if item.quantity > available:
                raise ValidationError(
                    f"{ticket_type.event.title} - {ticket_type.name}: "
                    f"only {available} ticket(s) available."
                )

            ticket_type.quantity_sold = F("quantity_sold") + item.quantity
            ticket_type.save(update_fields=["quantity_sold", "updated_at"])

    order.inventory_committed_at = timezone.now()
    order.inventory_released_at = None
    order.save(
        update_fields=[
            "inventory_committed_at",
            "inventory_released_at",
            "updated_at",
        ]
    )

    record_inventory_committed(
        order,
        created_by=created_by,
        source=source,
    )

    return True


@transaction.atomic
def release_order_inventory(order, created_by=None, source="system"):
    order = order.__class__.objects.select_for_update().get(pk=order.pk)

    if not order.inventory_committed_at:
        return False

    items = list(
        order.items.select_related(
            "merch_item",
            "ticket_type",
        )
    )

    for item in items:
        if item.merch_item_id:
            merch_item = MerchItem.objects.select_for_update().get(pk=item.merch_item_id)

            if merch_item.track_stock:
                merch_item.stock_quantity = F("stock_quantity") + item.quantity
                merch_item.save(update_fields=["stock_quantity", "updated_at"])

        elif item.ticket_type_id:
            ticket_type = TicketType.objects.select_for_update().get(pk=item.ticket_type_id)

            new_quantity_sold = max(ticket_type.quantity_sold - item.quantity, 0)
            ticket_type.quantity_sold = new_quantity_sold
            ticket_type.save(update_fields=["quantity_sold", "updated_at"])

    order.inventory_committed_at = None
    order.inventory_released_at = timezone.now()
    order.save(
        update_fields=[
            "inventory_committed_at",
            "inventory_released_at",
            "updated_at",
        ]
    )

    record_inventory_released(
        order,
        created_by=created_by,
        source=source,
    )

    return True


def sync_inventory_for_order_status(order, created_by=None, source="system"):
    if order.status == order.Status.PAID:
        return commit_order_inventory(
            order,
            created_by=created_by,
            source=source,
        )

    if order.status in {
        order.Status.CANCELLED,
        order.Status.EXPIRED,
        order.Status.REFUNDED,
    }:
        return release_order_inventory(
            order,
            created_by=created_by,
            source=source,
        )

    return False