from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from books.views import BookViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import UserRegistrationView, UserProfileView
from borrowing.views import BorrowingViewSet


router = routers.DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrowings', BorrowingViewSet, basename='borrowing')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include(router.urls)),
    path('api/users/', UserRegistrationView.as_view(), name='user-register'),
    path('api/users/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('api/users/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/users/me/', UserProfileView.as_view(), name='user-profile'),
    path('api/payment/', include('payment.urls')),
    
]
