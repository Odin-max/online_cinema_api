from celery import shared_task
from django.utils import timezone
from .telegram import send_message
from borrowing.models import Borrowing
from payment.models import Payment

@shared_task
def notify_new_borrowing(borrowing_id: int) -> None:
    b = Borrowing.objects.select_related('user', 'book').get(id=borrowing_id)
    text = (f"New borrowing created:\n"
            f"User: {b.user.email}\n"
            f"Book: {b.book.title}\n"
            f"Due: {b.expected_return_date}")
    send_message(text)

@shared_task
def notify_payment_success(payment_id: int) -> None:
    p = Payment.objects.select_related('borrowing__user', 'borrowing__book').get(id=payment_id)
    text = (f"Payment successful:\n"
            f"User: {p.borrowing.user.email}\n"
            f"Book: {p.borrowing.book.title}\n"
            f"Amount: ${p.money_to_pay}")
    send_message(text)

@shared_task
def check_overdue_borrowings() -> None:
    today = timezone.now().date()
    overdue = Borrowing.objects.filter(
        actual_return_date__isnull=True,
        expected_return_date__lt=today
    ).select_related('user', 'book')
    for b in overdue:
        text = (f"Overdue borrowing detected:\n"
                f"User: {b.user.email}\n"
                f"Book: {b.book.title}\n"
                f"Due since: {b.expected_return_date}")
        send_message(text)