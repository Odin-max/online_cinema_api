import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from books.models import Book
from borrowing.models import Borrowing
from payment.models import Payment

User = get_user_model()


@pytest.fixture
def book(db):
    return Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover="",
        inventory=5,
        daily_fee=1.50
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="pass123")


@pytest.fixture
def borrowing(db, book, user):
    borrow_date = date(2025, 7, 15)
    expected_return = borrow_date + timedelta(days=1)
    return Borrowing.objects.create(
        borrow_date=borrow_date,
        expected_return_date=expected_return,
        book=book,
        user=user
    )


@pytest.mark.django_db
def test_payment_valid_default_status_type(borrowing):
    payment = Payment(
        type=Payment.TypeChoices.PAYMENT,
        borrowing=borrowing,
        session_url="https://example.com/session",
        session_id="sess_123",
        money_to_pay=50.00
    )
    payment.full_clean()


@pytest.mark.django_db
def test_str_representation(borrowing):
    payment = Payment.objects.create(
        type=Payment.TypeChoices.FINE,
        borrowing=borrowing,
        session_url="https://example.com/session",
        session_id="sess_456",
        money_to_pay=15.50,
        status=Payment.StatusChoices.PAID
    )
    expected = f"Payment {payment.id} for borrowing {borrowing.id} (status: {Payment.StatusChoices.PAID})"
    assert str(payment) == expected


@pytest.mark.django_db
def test_invalid_status_choice_raises(borrowing):
    payment = Payment(
        status="INVALID",
        type=Payment.TypeChoices.PAYMENT,
        borrowing=borrowing,
        session_url="https://example.com/session",
        session_id="sess_789",
        money_to_pay=20.00
    )
    with pytest.raises(ValidationError):
        payment.full_clean()


@pytest.mark.django_db
def test_invalid_type_choice_raises(borrowing):
    payment = Payment(
        status=Payment.StatusChoices.PENDING,
        type="WRONG",
        borrowing=borrowing,
        session_url="https://example.com/session",
        session_id="sess_101",
        money_to_pay=30.00
    )
    with pytest.raises(ValidationError):
        payment.full_clean()
