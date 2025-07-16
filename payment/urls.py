from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreateCheckoutSessionView,
    StripeSuccessView,
    StripeCancelView,
    PaymentViewSet,
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('success/', StripeSuccessView.as_view(), name='stripe-success'),
    path('cancel/', StripeCancelView.as_view(), name='stripe-cancel'),
]