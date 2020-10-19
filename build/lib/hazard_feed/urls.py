from django.urls import path, include
from .views.subscribe import *
from .views.warnings import *
from rest_framework.routers import DefaultRouter
app_name = 'hazard_feed'

router = DefaultRouter()
router.register(r'hazard-levels', HazardLevelsViewSet, basename='hazard_levels')
router.register(r'warnings', HazardWarningsAPIViewSet, basename='hazard_warnings')

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/unsubscribe_newsletter', NewsletterUnsubscribeAPIView.as_view(), name='unsubscribe_newsletter'),
    path('v1/code-validate', CodeValidationAPIView.as_view(), name='code_validate'),
    path('v1/', include(router.urls))
]

