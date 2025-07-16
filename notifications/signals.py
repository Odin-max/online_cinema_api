from django.db.models.signals import post_save
from django.dispatch import receiver
from borrowing.models import Borrowing
from payment.models import Payment
from .tasks import notify_new_borrowing, notify_payment_success


@receiver(post_save, sender=Borrowing)
def borrowing_created(sender, instance, created, **kwargs) -> None:
    if created:
        notify_new_borrowing.delay(instance.id)

@receiver(post_save, sender=Payment)
def payment_updated(sender, instance, **kwargs) -> None:
    if instance.status == instance.StatusChoices.PAID:
        notify_payment_success.delay(instance.id)
