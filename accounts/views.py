from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(email=response.data['email'])
        data = UserSerializer(user).data
        return Response(data, status=response.status_code)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user