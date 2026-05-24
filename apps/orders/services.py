from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def format_money(currency, amount):
    return f"{currency} {amount:.2f}"


def get_order_items_summary(order):
    lines = []

    for item in order.items.all():
        lines.append(
            f"- {item.description} x {item.quantity} "
            f"@ {format_money(order.currency, item.unit_amount)} "
            f"= {format_money(order.currency, item.total_amount)}"
        )

    return "\n".join(lines)


def get_order_admin_url(order, request=None):
    path = reverse("admin:orders_order_change", args=[order.pk])

    if request:
        return request.build_absolute_uri(path)

    return path


def send_order_admin_notification(order, request=None):
    recipient = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "")

    if not recipient:
        return False

    subject = f"New order request: {order.reference_code}"

    message = f"""
A new order request has been submitted.

Order Reference:
{order.reference_code}

Customer:
{order.customer_name}
{order.customer_email}
{order.customer_phone or "-"}

Items:
{get_order_items_summary(order)}

Total:
{format_money(order.currency, order.total_amount)}

Status:
{order.get_status_display()}

Admin Link:
{get_order_admin_url(order, request=request)}
""".strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=True,
    )

    return True


def send_order_customer_confirmation(order):
    if not order.customer_email:
        return False

    subject = f"Your CeroPJ order request: {order.reference_code}"

    message = f"""
Hi {order.customer_name},

Thank you for your order request.

Order Reference:
{order.reference_code}

Items:
{get_order_items_summary(order)}

Total:
{format_money(order.currency, order.total_amount)}

Current Status:
{order.get_status_display()}

Payment is not collected online yet. Our team will follow up with payment or collection details.

Thank you,
CeroPJ
""".strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        fail_silently=True,
    )

    return True


def send_order_status_update(order):
    if not order.customer_email:
        return False

    subject = f"CeroPJ order update: {order.reference_code}"

    message = f"""
Hi {order.customer_name},

Your order status has been updated.

Order Reference:
{order.reference_code}

Current Status:
{order.get_status_display()}

Items:
{get_order_items_summary(order)}

Total:
{format_money(order.currency, order.total_amount)}

Thank you,
CeroPJ
""".strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer_email],
        fail_silently=True,
    )

    return True