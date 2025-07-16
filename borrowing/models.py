from django.db import models
from django.db.models import Q, F, CheckConstraint
from django.core.exceptions import ValidationError
from books.models import Book
from accounts.models import User

class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrowings'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='borrowings'
    )

    class Meta:
        constraints = [
            CheckConstraint(check=Q(expected_return_date__gte=F('borrow_date')), name='expected_return_after_borrow'),
            CheckConstraint(check=Q(actual_return_date__gte=F('borrow_date')), name='actual_return_after_borrow'),
        ]

    def clean(self):
        if self.expected_return_date < self.borrow_date:
            raise ValidationError({'expected_return_date': 'Expected return date must be on or after borrow date.'})
        if self.actual_return_date and self.actual_return_date < self.borrow_date:
            raise ValidationError({'actual_return_date': 'Actual return date cannot be before borrow date.'})

    def __str__(self):
        return f"{self.user.email} borrowed '{self.book.title}'"
    