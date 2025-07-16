from rest_framework import serializers
from .models import Payment
from borrowing.serializers import BorrowingReadSerializer

class CheckoutSerializer(serializers.Serializer):
    borrowing_id = serializers.IntegerField()

class CancelSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()

class SessionIdSerializer(serializers.Serializer):
    session_id = serializers.CharField()

class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingReadSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'borrowing', 'session_id', 'session_url', 'money_to_pay', 'status', 'type']
        read_only_fields = ['id', 'borrowing', 'session_id', 'session_url', 'money_to_pay', 'status', 'type']