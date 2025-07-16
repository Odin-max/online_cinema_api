from django.db import models # type: ignore


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        HARD = 'HARD', 'Hardcover'
        SOFT = 'SOFT', 'Softcover'

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=4,
        choices=CoverChoices.choices
    )
    inventory = models.PositiveSmallIntegerField(
        help_text="Number of copies currently available"
    )
    daily_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Daily fee in $USD"
    )

    def __str__(self):
        return self.title
