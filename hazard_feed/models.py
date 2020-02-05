import datetime
import pytz
import uuid
from django.db import models
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext_lazy as _


class TimeStampBase(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_modified = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

class HazardLevels(models.Model):
    title = models.CharField(max_length=32)
    danger_level = models.IntegerField(validators=[MaxValueValidator(10)])
    color_code = models.CharField(max_length=6, null=True)
    description = models.TextField()

    class Meta:
        verbose_name = _('Hazard Level')
        verbose_name_plural = _('Hazard Levels')

class HazardFeeds(TimeStampBase):
    id = models.BigIntegerField(primary_key=True)
    date = models.DateTimeField()
    title = models.CharField(max_length=128)
    link = models.URLField()
    summary = models.TextField()
    hazard_level = models.ForeignKey(HazardLevels, on_delete=models.CASCADE)
    is_sent = models.BooleanField(default=False)
    date_send = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _('Hazard Feed')
        verbose_name_plural = _('Hazard Feeds')

    def resency(self):
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return now-self.date

    def is_newer_that(self, timedelta):
        return self.date_created-self.date < timedelta

    def date_send_set(self):
        self.date_send = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

    @classmethod
    def not_sent(cls):
        return cls.objects.filter(is_sent=False)



class WeatherRecipients(models.Model):
    email = models.EmailField()
    title = models.CharField(max_length=64, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Weather hazard recipient')
        verbose_name_plural = _('Weather hazard recipients')

