from rest_framework import serializers
from .models import Borrowing
from books.serializers import BookSerializer
from accounts.serializers import UserSerializer

class BorrowingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ['id', 'book', 'borrow_date', 'expected_return_date', 'actual_return_date']

    def validate(self, attrs):
        book = attrs.get('book')
        if book.inventory < 1:
            raise serializers.ValidationError('Book not available.')
        return attrs

    def create(self, validated_data):
        book = validated_data['book']
        book.inventory -= 1
        book.save()
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = ['id', 'user', 'book', 'borrow_date', 'expected_return_date', 'actual_return_date']
    