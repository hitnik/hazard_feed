from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import time
from .models import EmailActivationCode, WeatherRecipients
from django.urls import reverse_lazy
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
import jwt

@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='newsletter_subscribe',
                                                operation_description="Subscripe Newsletter view",
                                                responses={status.HTTP_200_OK: SubcribeResponseSerializer,
                                                           status.HTTP_302_FOUND: None}
                  ))
class NewsletterSubscribeAPIView(generics.GenericAPIView):
    serializer_class = SubscribeSerialiser

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def create_code_response(self, recipient):
        code = EmailActivationCode.objects.create(target=recipient, is_activate=True)
        token = jwt.encode({'id': code.id.__str__(), 'exp': code.date_expiration},
                           settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        data = {'expires': int(code.date_expiration.timestamp() * 1000),
                'token': token,
                'code_confirm': reverse_lazy('hazard_feed:code_validate')
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @csrf_exempt
    def post(self,request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            title = serializer.validated_data.get('title')
            queryset = self.get_queryset()
            if queryset.filter(email=email).exists():
                obj = queryset.get(email=email)
                if obj.is_active:
                    return Response(status=status.HTTP_302_FOUND)
                else:
                    obj.title = title
                    obj.save()
                    return self.create_code_response(obj)
            else:
                obj = WeatherRecipients.objects.create(email=email, title=title)
                return self.create_code_response(obj)
            return Response(status=status.HTTP_200_OK)




@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='newsletter_unsubscribe',
                                                operation_description="Unsubscripe Newsletter view",
                                                responses={status.HTTP_200_OK: SubcribeResponseSerializer}
                  ))
class NewsletterUnsubscribeAPIView(generics.GenericAPIView):
    serializer_class = WeatherRecipientsMailSerializer

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and exc.detail['email'][0] == 'email does not exist':
            exc.status_code = status.HTTP_404_NOT_FOUND
        return super().handle_exception(exc)

    def create_code_response(self, recipient):
        code = EmailActivationCode.objects.create(target=recipient, is_activate=False)
        token = jwt.encode({'id': code.id.__str__(), 'exp': code.date_expiration},
                           settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        data = {'expires': int(code.date_expiration.timestamp() * 1000),
                'token': token,
                'code_confirm': reverse_lazy('hazard_feed:code_validate')
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @csrf_exempt
    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            target = WeatherRecipients.objects.get(email=email)
            if target.is_active:
                return self.create_code_response(target)
            else:
                return Response(status=status.HTTP_303_SEE_OTHER)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='activate_subscribe',
                                                operation_description="Subscribe Newsletter code confirmation view",
                                                responses={status.HTTP_200_OK: SuccesResponseSerializer}
                  ))
class CodeValidationAPIView(generics.GenericAPIView):
    serializer_class = ActivationCodeSerializer

    def perform_action(self, instance, code):
       result = instance.activate_deactivate(code)
       return result

    @csrf_exempt
    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                data = jwt.decode(serializer.data['token'], settings.SECRET_KEY, algorithm='HS256')
            except jwt.ExpiredSignatureError:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Code is expired'})
            except jwt.InvalidTokenError:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid token'})
            code = serializer.data['code']
            id = data['id']
            if EmailActivationCode.objects.filter(id=id).exists():
                activation = EmailActivationCode.objects.get(id=id)
                if activation.is_activate:
                    message = 'Your newsletter subscription has been activated'
                else:
                    message = 'your newsletter subscription has been deactivated'
                if self.perform_action(activation, code):
                    serializer = SuccesResponseSerializer(data={'ok':True, 'message': message})
                    if serializer.is_valid():
                        return Response(status=status.HTTP_200_OK, data=serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})
