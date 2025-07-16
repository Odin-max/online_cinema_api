import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status, permissions, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from .serializers import CheckoutSerializer, CancelSerializer, PaymentSerializer, SessionIdSerializer
from .models import Payment
from borrowing.models import Borrowing

stripe_key = settings.STRIPE_SECRET_KEY
if not stripe_key:
    raise ImproperlyConfigured("STRIPE_SECRET_KEY must be set in environment.")
stripe.api_key = stripe_key

class CreateCheckoutSessionView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrowing_id = serializer.validated_data['borrowing_id']
        try:
            borrowing = Borrowing.objects.select_related('book').get(id=borrowing_id, user=request.user)
        except Borrowing.DoesNotExist:
            return Response({'detail': 'Borrowing not found.'}, status=status.HTTP_404_NOT_FOUND)

        days = (borrowing.expected_return_date - borrowing.borrow_date).days
        amount_cents = int(days * float(borrowing.book.daily_fee) * 100)

        success_url = request.build_absolute_uri(reverse('stripe-success', request=request)) + f"?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse('stripe-cancel', request=request))

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': borrowing.book.title},
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email,
        )

        payment = Payment.objects.create(
            borrowing=borrowing,
            session_id=session.id,
            session_url=session.url,
            money_to_pay=amount_cents / 100,
            type=Payment.TypeChoices.PAYMENT,
            status=Payment.StatusChoices.PENDING,
        )
        return Response({'checkout_url': session.url, 'payment_id': payment.id})

class StripeSuccessView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SessionIdSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data['session_id']

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if session.payment_status != 'paid':
            return Response({'detail': 'Payment not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        payment.status = Payment.StatusChoices.PAID
        payment.save(update_fields=['status'])
        return Response({'detail': 'Payment successful.'})

class StripeCancelView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CancelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_id = serializer.validated_data['payment_id']
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            stripe.checkout.Session.expire(payment.session_id)
        except stripe.error.StripeError:
            pass
        try:
            session = stripe.checkout.Session.retrieve(payment.session_id)
            pi_id = session.payment_intent
            if not pi_id:
                payment.status = Payment.StatusChoices.CANCELLED
                payment.save(update_fields=['status'])
                return Response({'detail': 'Checkout session cancelled.'})
            intent = stripe.PaymentIntent.retrieve(pi_id, expand=['charges'])
            charges = intent.charges.data
            charge_id = charges[0].id if charges else None
            if not charge_id:
                return Response({'detail': 'No charges to refund.'}, status=status.HTTP_400_BAD_REQUEST)
            stripe.Refund.create(charge=charge_id)
            payment.status = Payment.StatusChoices.CANCELLED
            payment.save(update_fields=['status'])
            return Response({'detail': 'Payment refunded and cancelled.'})
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(borrowing__user=user)