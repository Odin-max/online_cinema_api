from django.db import models
from borrowing.models import Borrowing


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class TypeChoices(models.TextChoices):
        PAYMENT = 'PAYMENT', 'Payment'
        FINE = 'FINE', 'Fine'

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    type = models.CharField(
        max_length=10,
        choices=TypeChoices.choices
    )
    borrowing = models.ForeignKey(
        Borrowing,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    session_url = models.URLField(help_text="URL for Stripe payment session")
    session_id = models.CharField(max_length=255, help_text="ID session Stripe")
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2, help_text="Sum to pay in $USD")

    def __str__(self):
        return f"Payment {self.id} for borrowing {self.borrowing.id} (status: {self.status})"