import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from books.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
import stripe

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@example.com', password='pass')

@pytest.fixture
def other_user(db):
    return User.objects.create_user(email='other@example.com', password='pass')

@pytest.fixture
def book(db):
    return Book.objects.create(
        title='Test Book',
        author='Author',
        cover='',
        inventory=3,
        daily_fee=2.0
    )

@pytest.fixture
def borrowing(db, book, user):
    return Borrowing.objects.create(
        borrow_date='2025-07-01',
        expected_return_date='2025-07-05',
        book=book,
        user=user
    )

@pytest.fixture
def payment_record(db, borrowing):
    return Payment.objects.create(
        borrowing=borrowing,
        session_id='sess_1',
        session_url='http://example.com',
        money_to_pay=10.0,
        type=Payment.TypeChoices.PAYMENT,
        status=Payment.StatusChoices.PENDING,
    )

@pytest.mark.django_db
def test_create_checkout_session_success(monkeypatch, api_client, user, borrowing):
    api_client.force_authenticate(user=user)
    class DummySession:
        id = 'sess_123'
        url = 'http://checkout'
    monkeypatch.setattr(stripe.checkout.Session, 'create', lambda **kwargs: DummySession())

    url = reverse('create-checkout-session')
    resp = api_client.post(url, {'borrowing_id': borrowing.id}, format='json')
    assert resp.status_code == 200
    assert 'checkout_url' in resp.data
    assert Payment.objects.filter(session_id='sess_123').exists()

@pytest.mark.django_db
def test_create_checkout_session_not_found(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse('create-checkout-session')
    resp = api_client.post(url, {'borrowing_id': 9999}, format='json')
    assert resp.status_code == 404
    assert resp.data['detail'] == 'Borrowing not found.'

@pytest.mark.django_db
def test_stripe_success_paid(monkeypatch, api_client, user, payment_record):
    api_client.force_authenticate(user=user)
    class DummySession:
        payment_status = 'paid'
    monkeypatch.setattr(stripe.checkout.Session, 'retrieve', lambda session_id: DummySession())

    url = reverse('stripe-success') + '?session_id=sess_1'
    resp = api_client.get(url)
    assert resp.status_code == 200
    payment_record.refresh_from_db()
    assert payment_record.status == Payment.StatusChoices.PAID

@pytest.mark.django_db
def test_stripe_success_not_paid(monkeypatch, api_client, user, payment_record):
    api_client.force_authenticate(user=user)
    class DummySession:
        payment_status = 'unpaid'
    monkeypatch.setattr(stripe.checkout.Session, 'retrieve', lambda session_id: DummySession())

    url = reverse('stripe-success') + '?session_id=sess_1'
    resp = api_client.get(url)
    assert resp.status_code == 400
    assert resp.data['detail'] == 'Payment not completed.'

@pytest.mark.django_db
def test_stripe_success_no_record(monkeypatch, api_client, user):
    api_client.force_authenticate(user=user)
    class DummySession:
        payment_status = 'paid'
    monkeypatch.setattr(stripe.checkout.Session, 'retrieve', lambda session_id: DummySession())

    url = reverse('stripe-success') + '?session_id=unknown'
    resp = api_client.get(url)
    assert resp.status_code == 404
    assert resp.data['detail'] == 'Payment record not found.'

@pytest.mark.django_db
def test_stripe_cancel_no_payment(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse('stripe-cancel')
    resp = api_client.post(url, {'payment_id': 9999}, format='json')
    assert resp.status_code == 404
    assert resp.data['detail'] == 'Payment not found.'

@pytest.mark.django_db
def test_stripe_cancel_simple(monkeypatch, api_client, user, payment_record):
    api_client.force_authenticate(user=user)
    monkeypatch.setattr(stripe.checkout.Session, 'expire', lambda session_id: None)
    class DummySession:
        payment_intent = None
    monkeypatch.setattr(stripe.checkout.Session, 'retrieve', lambda session_id: DummySession())

    url = reverse('stripe-cancel')
    resp = api_client.post(url, {'payment_id': payment_record.id}, format='json')
    assert resp.status_code == 200
    payment_record.refresh_from_db()
    assert payment_record.status == Payment.StatusChoices.CANCELLED
    assert resp.data['detail'] == 'Checkout session cancelled.'

@pytest.mark.django_db
def test_stripe_cancel_refund(monkeypatch, api_client, user, payment_record):
    api_client.force_authenticate(user=user)
    monkeypatch.setattr(stripe.checkout.Session, 'expire', lambda session_id: None)
    class DummySession:
        payment_intent = 'pi_1'
    monkeypatch.setattr(stripe.checkout.Session, 'retrieve', lambda session_id: DummySession())

    class DummyIntent:
        charges = type('Charges', (), {'data': [type('Ch', (), {'id': 'ch_1'})]})
    monkeypatch.setattr(stripe.PaymentIntent, 'retrieve', lambda pid, expand: DummyIntent())
    monkeypatch.setattr(stripe.Refund, 'create', lambda **kwargs: None)

    url = reverse('stripe-cancel')
    resp = api_client.post(url, {'payment_id': payment_record.id}, format='json')
    assert resp.status_code == 200
    payment_record.refresh_from_db()
    assert payment_record.status == Payment.StatusChoices.CANCELLED
    assert resp.data['detail'] == 'Payment refunded and cancelled.'

@pytest.mark.django_db
def test_payment_viewset_filters(api_client, user, other_user, borrowing, payment_record):
    api_client.force_authenticate(user=user)
    url = reverse('payment-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert all(
    (item['borrowing']['id'] if isinstance(item['borrowing'], dict) else item['borrowing']) == borrowing.id
    for item in resp.data
)

    other_payment = Payment.objects.create(
        borrowing=borrowing,
        session_id='sess_2',
        session_url='url',
        money_to_pay=5.0,
        type=Payment.TypeChoices.FINE,
        status=Payment.StatusChoices.PENDING
    )
    other_user.is_staff = True
    other_user.save()
    api_client.force_authenticate(user=other_user)
    resp2 = api_client.get(url)
    assert any(p['id'] == other_payment.id for p in resp2.data)