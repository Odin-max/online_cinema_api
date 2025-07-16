from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payment.models import Payment
from .models import Borrowing
from .serializers import BorrowingWriteSerializer, BorrowingReadSerializer

class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'return_book']:
            return BorrowingReadSerializer
        return BorrowingWriteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        is_staff = user.is_staff
        user_id = self.request.query_params.get('user_id')
        is_active = self.request.query_params.get('is_active')

        if not is_staff:
            qs = qs.filter(user=user)
        else:
            if user_id:
                qs = qs.filter(user_id=user_id)

        if is_active is not None:
            active = is_active.lower() in ['true', '1']
            if active:
                qs = qs.filter(actual_return_date__isnull=True)
            else:
                qs = qs.filter(actual_return_date__isnull=False)

        return qs

    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            return Response({'detail': 'Book already returned.'}, status=status.HTTP_400_BAD_REQUEST)

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()
        book = borrowing.book
        book.inventory += 1
        book.save()

        overdue_days = (borrowing.actual_return_date - borrowing.expected_return_date).days
        if overdue_days > 0:
            multiplier = getattr(settings, 'FINE_MULTIPLIER', 1)
            fine_amount = overdue_days * float(book.daily_fee) * multiplier
            Payment.objects.create(
                borrowing=borrowing,
                session_id='',
                session_url='',
                money_to_pay=fine_amount,
                type=Payment.TypeChoices.FINE,
                status=Payment.StatusChoices.PENDING,
            )

        return Response(self.get_serializer(borrowing).data)