from .models import OrderHistory


def record_order_history(
    order,
    event_type,
    message="",
    from_status="",
    to_status="",
    created_by=None,
    metadata=None,
):
    return OrderHistory.objects.create(
        order=order,
        event_type=event_type,
        from_status=from_status or "",
        to_status=to_status or "",
        message=message,
        created_by=created_by,
        metadata=metadata or {},
    )


def record_order_created(order, created_by=None, source="public"):
    return record_order_history(
        order=order,
        event_type=OrderHistory.EventType.CREATED,
        to_status=order.status,
        created_by=created_by,
        message=f"Order created from {source}.",
        metadata={
            "source": source,
            "reference_code": order.reference_code,
            "total_amount": str(order.total_amount),
            "currency": order.currency,
        },
    )


def record_order_status_change(
    order,
    from_status,
    to_status,
    created_by=None,
    source="admin",
):
    if from_status == to_status:
        return None

    return record_order_history(
        order=order,
        event_type=OrderHistory.EventType.STATUS_CHANGED,
        from_status=from_status,
        to_status=to_status,
        created_by=created_by,
        message=f"Order status changed from {from_status} to {to_status}.",
        metadata={
            "source": source,
        },
    )


def record_inventory_committed(order, created_by=None, source="system"):
    return record_order_history(
        order=order,
        event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
        to_status=order.status,
        created_by=created_by,
        message="Inventory committed for this order.",
        metadata={
            "source": source,
            "inventory_committed_at": (
                order.inventory_committed_at.isoformat()
                if order.inventory_committed_at
                else None
            ),
        },
    )


def record_inventory_released(order, created_by=None, source="system"):
    return record_order_history(
        order=order,
        event_type=OrderHistory.EventType.INVENTORY_RELEASED,
        to_status=order.status,
        created_by=created_by,
        message="Inventory released for this order.",
        metadata={
            "source": source,
            "inventory_released_at": (
                order.inventory_released_at.isoformat()
                if order.inventory_released_at
                else None
            ),
        },
    )


def record_order_email_event(
    order,
    email_type,
    sent,
    recipient="",
    created_by=None,
):
    event_type = (
        OrderHistory.EventType.EMAIL_SENT
        if sent
        else OrderHistory.EventType.EMAIL_SKIPPED
    )

    return record_order_history(
        order=order,
        event_type=event_type,
        to_status=order.status,
        created_by=created_by,
        message=(
            f"{email_type} email sent."
            if sent
            else f"{email_type} email skipped."
        ),
        metadata={
            "email_type": email_type,
            "recipient": recipient,
            "sent": sent,
        },
    )


def record_order_error(order, message, created_by=None, metadata=None):
    return record_order_history(
        order=order,
        event_type=OrderHistory.EventType.ERROR,
        to_status=order.status,
        created_by=created_by,
        message=message,
        metadata=metadata or {},
    )