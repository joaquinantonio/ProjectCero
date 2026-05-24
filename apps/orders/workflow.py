from django.db import transaction

from .audit import record_order_status_change
from .inventory import sync_inventory_for_order_status
from .models import Order


def change_order_status(
    order_id,
    new_status,
    created_by=None,
    source="system",
):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        old_status = order.status

        if old_status == new_status:
            return order, False, False

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        inventory_changed = sync_inventory_for_order_status(
            order,
            created_by=created_by,
            source=source,
        )

        record_order_status_change(
            order,
            from_status=old_status,
            to_status=new_status,
            created_by=created_by,
            source=source,
        )

        return order, True, inventory_changed