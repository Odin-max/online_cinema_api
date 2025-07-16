import pytest
from datetime import datetime, date
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from books.models import Book
from borrowing.models import Borrowing
from payment.models import Payment

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def book(db):
    return Book.objects.create(
        title="Book",
        author="Author",
        cover="",
        inventory=3,
        daily_fee=2.0
    )

@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="pass")

@pytest.fixture
def staff_user(db):
    return User.objects.create_superuser(email="staff@example.com", password="pass")

@pytest.fixture
def active_borrowing(db, book, user):
    return Borrowing.objects.create(
        borrow_date=date(2025, 7, 1),
        expected_return_date=date(2025, 7, 5),
        book=book,
        user=user
    )

@pytest.fixture
def returned_borrowing(db, book, user):
    return Borrowing.objects.create(
        borrow_date=date(2025, 6, 20),
        expected_return_date=date(2025, 6, 25),
        actual_return_date=date(2025, 6, 26),
        book=book,
        user=user
    )

@pytest.mark.django_db
def test_list_non_staff_sees_only_own(api_client, book, user):
    other = User.objects.create_user(email="other@example.com", password="pass")
    Borrowing.objects.create(
        borrow_date=date(2025, 1, 1),
        expected_return_date=date(2025, 1, 2),
        book=book,
        user=other
    )
    b = Borrowing.objects.create(
        borrow_date=date(2025, 1, 3),
        expected_return_date=date(2025, 1, 4),
        book=book,
        user=user
    )
    api_client.force_authenticate(user=user)
    resp = api_client.get(reverse('borrowing-list'))
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]['id'] == b.id

@pytest.mark.django_db
def test_list_staff_filters(api_client, active_borrowing, user, staff_user):
    api_client.force_authenticate(user=staff_user)
    resp = api_client.get(reverse('borrowing-list'))
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    resp2 = api_client.get(reverse('borrowing-list'), {'user_id': user.id})
    assert resp2.status_code == 200
    assert all(item['user']['id'] == user.id for item in resp2.data)

    
@pytest.mark.django_db
def test_filter_is_active(api_client, active_borrowing, returned_borrowing, user):
    api_client.force_authenticate(user=user)
    resp = api_client.get(reverse('borrowing-list'), {'is_active': 'true'})
    assert resp.status_code == 200
    assert all(item['actual_return_date'] is None for item in resp.data)
    resp2 = api_client.get(reverse('borrowing-list'), {'is_active': 'false'})
    assert resp2.status_code == 200
    assert all(item['actual_return_date'] is not None for item in resp2.data)

@pytest.mark.django_db
def test_return_book_action_creates_fine(api_client, active_borrowing, user, monkeypatch, book):
    fake_now = datetime(2025, 7, 10, tzinfo=timezone.get_current_timezone())
    monkeypatch.setattr(timezone, 'now', lambda: fake_now)
    api_client.force_authenticate(user=user)
    url = reverse('borrowing-return-book', args=[active_borrowing.id])
    resp = api_client.post(url)
    assert resp.status_code == 200
    active_borrowing.refresh_from_db()
    assert active_borrowing.actual_return_date == fake_now.date()
    book.refresh_from_db()
    assert book.inventory == 4
    payments = Payment.objects.filter(borrowing=active_borrowing)
    assert payments.exists()
    fine = payments.first().money_to_pay
    assert fine == 5 * book.daily_fee * settings.FINE_MULTIPLIER

@pytest.mark.django_db
def test_return_book_action_idempotent(api_client, returned_borrowing, user):
    api_client.force_authenticate(user=user)
    url = reverse('borrowing-return-book', args=[returned_borrowing.id])
    resp = api_client.post(url)
    assert resp.status_code == 400
    assert 'already returned' in resp.data['detail'].lower()
