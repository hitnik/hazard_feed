from django.urls import path, include
from .views.subscribe import *
from .views.warnings import *
from rest_framework.routers import DefaultRouter
app_name = 'hazard_feed'

router = DefaultRouter()
router.register(r'hazard-levels', HazardLevelsViewSet, basename='hazard_levels')
router.register(r'warnings', HazardWarningsAPIViewSet, basename='hazard_warnings')

urlpatterns = [
    path('v1/newsletter-subscribe', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/newsletter-unsubscribe', NewsletterUnsubscribeAPIView.as_view(), name='unsubscribe_newsletter'),
    path('v1/newsletter-subscribe/edit', NewsletterSubscribeEditApiView.as_view(), name='subscribe_edit'),
    path('v1/validate-subscribe', SubscribeValidationAPIView.as_view(), name='validate_subscribe'),
    path('v1/validate-unsubscribe', UnsubscribeValidationApiView.as_view(), name='validate_unsubscribe'),
    path('v1/validate-edit', EditValidationApiView.as_view(), name='validate_edit'),
    path('v1/weather-recipients', WeatherRecipientsRetrieveAPIView.as_view(), name='weather_recipients'),
    path('v1/', include(router.urls)),
]
