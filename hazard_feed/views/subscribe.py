from rest_framework import generics, viewsets
from django.http import Http404
import django_rq
from redis.exceptions import ConnectionError
from hazard_feed.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from hazard_feed.models import (EmailActivationCode, WeatherRecipients,
                                WeatherRecipientsEditCandidate
                                )
from django.urls import reverse_lazy
from hazard_feed.jobs import (send_email_code_activate, send_email_code_deactivate,
                              send_email_code_edit,
                              )


class NewsletterSubscribeAPIView(generics.GenericAPIView):
    serializer_class = SubscribeSerialiser
    validate_url = reverse_lazy('hazard_feed:validate_subscribe')

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def serialized_data(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            title = serializer.validated_data.get('title')
            levels = list(serializer.validated_data.get('hazard_levels'))
            if len(levels) == 0:
                levels = list(HazardLevels.objects.all().values_list('id', flat=True))
            return email, title, levels

    def generate_code(self):
        return EmailActivationCode.objects.create()

    def create_code_response(self, code, target):
        data = {'expires': int(code.date_expiration.timestamp() * 1000),
                'target_uid': target.uuid,
                'code_confirm': self.validate_url
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def send_notify(self, code, recipient):
        try:
            queue = django_rq.get_queue()
            queue.enqueue(send_email_code_activate, code, [recipient])
        except ConnectionError:
            send_email_code_activate(code, [recipient])

    @csrf_exempt
    def post(self, request, format=None):
        email, title, levels = self.serialized_data(request)
        queryset = self.get_queryset()
        if queryset.filter(email=email).exists():
            obj = queryset.get(email=email)
            if obj.is_active:
                return Response(status=status.HTTP_302_FOUND, data={"Error": "Email already subscribed"})
            else:
                obj.title = title
                obj.hazard_levels.clear()
                obj.hazard_levels.add(*levels)
                if obj.code:
                    obj.code.delete()
                code = self.generate_code()
                obj.code = code
                obj.save()
                self.send_notify(code.code, obj.email)
                return self.create_code_response(code, obj)
        else:
            obj = WeatherRecipients.objects.create(email=email, title=title)
            obj.hazard_levels.add(*levels)
            code = self.generate_code()
            obj.code = code
            obj.save()
            self.send_notify(code.code, obj.email)
            return self.create_code_response(code, obj)

class NewsletterUnsubscribeAPIView(NewsletterSubscribeAPIView):
    serializer_class = WeatherRecipientsMailSerializer
    validate_url = reverse_lazy('hazard_feed:validate_unsubscribe')

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and exc.detail['email'][0] == 'email does not exist':
            exc.status_code = status.HTTP_404_NOT_FOUND
        return super().handle_exception(exc)

    def serialized_data(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return serializer.validated_data.get('email')

    def send_notify(self, code, recipient):
        try:
            queue = django_rq.get_queue()
            queue.enqueue(send_email_code_deactivate, code, [recipient])
        except ConnectionError:
            send_email_code_deactivate(code, [recipient])

    @csrf_exempt
    def post(self, request, format=None):
        email = self.serialized_data(request)
        try:
            obj = WeatherRecipients.objects.get(email=email)
        except WeatherRecipients.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"Error": "Email not registered"})
        if obj.is_active:
            if obj.code:
                obj.code.delete()
            code = self.generate_code()
            obj.code = code
            obj.save()
            self.send_notify(code.code, obj.email)
            return self.create_code_response(code, obj)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"Error": "Email not registered"})
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SubscribeValidationAPIView(generics.GenericAPIView):
    serializer_class = ActivationCodeSerializer

    def response_success(self):
        message = 'Подписка на рассылку успешно активирована'
        serializer = SuccesResponseSerializer(data={'ok': True, 'message': message})
        serializer.is_valid()
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def get_serialized_data(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            code = serializer.data['code']
            uid = serializer.data['target_uid']
            return code, uid

    @csrf_exempt
    def post(self, request, format=None):
        code, uid = self.get_serialized_data(request)
        try:
            obj = WeatherRecipients.objects.get(uuid=uid)
        except WeatherRecipients.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid uid'})
        if obj.code and obj.code.is_valid(code):
            obj.is_active = True
            obj.code.delete()
            obj.code = None
            obj.save()
            return  self.response_success()
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})

class UnsubscribeValidationApiView(SubscribeValidationAPIView):

    def response_success(self):
        message = 'Подписка на рассылку деактивирована'
        serializer = SuccesResponseSerializer(data={'ok': True, 'message': message})
        serializer.is_valid()
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @csrf_exempt
    def post(self, request, format=None):
        code, uid = self.get_serialized_data(request)
        try:
            obj = WeatherRecipients.objects.get(uuid=uid)
        except WeatherRecipients.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid uid'})
        if obj.code and obj.code.is_valid(code):
            obj.is_active = False
            obj.save()
            obj.code.delete()
            obj.code = None
            obj.save()
            return self.response_success()
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})


class NewsletterSubscribeEditApiView(NewsletterSubscribeAPIView):
    validate_url = reverse_lazy('hazard_feed:validate_edit')

    def send_notify(self, code, recipient):
        try:
            queue = django_rq.get_queue()
            queue.enqueue(send_email_code_edit, code, [recipient])
        except ConnectionError:
            send_email_code_edit(code, [recipient])

    @csrf_exempt
    def post(self, request, format=None):
        email, title, levels = self.serialized_data(request)
        queryset = self.get_queryset()
        if queryset.filter(email=email).exists():
            obj = queryset.get(email=email)
            if obj.is_active:
                if WeatherRecipientsEditCandidate.objects.filter(target__email=email).exists():
                    WeatherRecipientsEditCandidate.objects.get(target__email=email).delete()
                candidate = WeatherRecipientsEditCandidate.objects.create(
                    target=obj,
                    title=title,
                )
                candidate.hazard_levels.add(*levels)
                candidate.save()
                if obj.code:
                    obj.code.delete()
                    obj.code = None
                code = self.generate_code()
                obj.code = code
                obj.save()
                self.send_notify(code.code, obj.email)
                return self.create_code_response(code, obj)
        return Response(status=status.HTTP_404_NOT_FOUND, data={'Error': 'Email is not registered'})


class EditValidationApiView(SubscribeValidationAPIView):

    def response_success(self):
        message = 'Параметры подписки успешно изменены'
        serializer = SuccesResponseSerializer(data={'ok': True, 'message': message})
        serializer.is_valid()
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @csrf_exempt
    def post(self, request, format=None):
        code, uid = self.get_serialized_data(request)
        try:
            obj = WeatherRecipients.objects.get(uuid=uid)
        except WeatherRecipients.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid uid'})
        if obj.code and obj.code.is_valid(code):
            candidate = WeatherRecipientsEditCandidate.objects.get(target__uuid= uid)
            obj.title = candidate.title
            obj.hazard_levels.clear()
            obj.hazard_levels.add(*list(candidate.hazard_levels.all().values_list('id', flat=True)))
            obj.save()
            obj.code.delete()
            obj.code = None
            obj.save()
            candidate.delete()
            return self.response_success()
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})

class WeatherRecipientsRetrieveAPIView(generics.RetrieveAPIView):
    http_method_names = [u'trace', u'head', u'options', u'post']
    queryset = WeatherRecipients.objects.all().filter(is_active=True)
    serializer_class_response = WeatherRecipientsModelSerializer
    serializer_class = WeatherRecipientsMailSerializer

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.serializer_class_response(self.object)
        return Response(serializer.data)

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        if queryset is None:
            queryset = self.get_queryset()

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if email is not None:
            queryset = queryset.filter(email=email)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404("No %(verbose_name)s found matching the query" %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

