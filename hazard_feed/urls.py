from django.urls import path, re_path
from .views import *
from rest_framework import permissions
from drf_yasg.views import get_schema_view as yasg_get_schema_view
from drf_yasg import openapi

app_name = 'hazard_feed'


yasg_schema_view = yasg_get_schema_view(
   openapi.Info(
      title="Weather API",
      default_version='v1',
      description="Weather hazard feeds API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/unsubscribe_newsletter', NewsletterUnsubscribeAPIView.as_view(), name='unsubscribe_newsletter'),
    path('v1/code-validate', CodeValidationAPIView.as_view(), name='code_validate'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', yasg_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', yasg_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', yasg_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]

