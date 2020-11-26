from rest_framework import serializers
from .models import WeatherRecipients, HazardFeeds, HazardLevels
from django.conf import settings
from django.core.validators import EmailValidator
from django.db.utils import OperationalError, ProgrammingError

class WeatherRecipientsMailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)

    def validate_email(self, value):
        try:
            obj = WeatherRecipients.objects.get(email=value)
        except WeatherRecipients.DoesNotExist:
            raise serializers.ValidationError(detail='email does not exist')
        return value

class SubscribeSerialiser(serializers.Serializer):
    title = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False, validators=[EmailValidator])
    hazard_levels = serializers.MultipleChoiceField(required=True,
                                                    allow_blank=False,
                                                    choices=[]
                                                    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['hazard_levels'].choices = HazardLevels.objects.all().values_list('id', flat=True)

    def create(self, validated_data):
        return validated_data

class WeatherRecipientsMailTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['email', 'title']

class ActivationCodeSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True,
                                 max_length=settings.ACTIVATION_CODE_LENTH,
                                 min_length=settings.ACTIVATION_CODE_LENTH)
    target_uid = serializers.CharField(required=True)

    def create(self, validated_data):
        return validated_data

    def validate_code(self, value):
        try:
            code = int(value)
        except ValueError:
            raise serializers.ValidationError('Not a digit')
        return value

class SubcribeResponseSerializer(serializers.Serializer):

    expires = serializers.DateTimeField()
    target_uid = serializers.CharField()
    code_confirm = serializers.URLField()

class SuccesResponseSerializer(serializers.Serializer):

    ok = serializers.BooleanField()
    message = serializers.CharField()

class HazardLevelModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = HazardLevels
        fields = ['id', 'title', 'danger_level',
                  'color_code', 'description'
                 ]

class HazardWarningsSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hazard_feed:hazard_warnings-detail")

    class Meta:
        model = HazardFeeds
        fields = ['id', 'url', 'title', 'external_link', 'summary',
                  'hazard_level', 'date_start', 'date_end']
        extra_kwargs = {
            'hazard_level': {'view_name': 'hazard_feed:hazard_levels-detail'},
        }

class WeatherRecipientsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['title', 'email', 'hazard_levels']