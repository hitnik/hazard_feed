from django.apps import AppConfig
from django.db.models.signals import post_save
import os
import django_rq
import datetime
from redis.exceptions import ConnectionError
from django.conf import settings



class HazardFeedConfig(AppConfig):
    """
     app settings. You must specify settings in your environment
    """
    name = 'hazard_feed'
    WEATHER_EMAIL_SMTP_HOST = os.getenv('WEATHER_EMAIL_SMTP_HOST')
    WEATHER_USE_TSL = int(os.getenv('WEATHER_USE_TSL', 0))
    WEATHER_EMAIL_SMTP_PORT = os.getenv('WEATHER_EMAIL_SMTP_PORT')
    WEATHER_EMAIL_HOST_USER = os.getenv('WEATHER_EMAIL_HOST_USER')
    WEATHER_EMAIL_HOST_PASSWORD = os.getenv('WEATHER_EMAIL_HOST_PASSWORD')


    def ready(self):

        if hasattr(settings, 'WEATHER_EMAIL_SMTP_HOST'):
            self.WEATHER_EMAIL_SMTP_HOST = settings.WEATHER_EMAIL_SMTP_HOST
        if hasattr(settings, 'WEATHER_USE_TSL'):
            self.WEATHER_USE_TSL = int(settings.WEATHER_USE_TSL)
        if hasattr(settings, 'WEATHER_EMAIL_SMTP_PORT'):
            self.WEATHER_EMAIL_SMTP_PORT = settings.WEATHER_EMAIL_SMTP_PORT
        if hasattr(settings, 'WEATHER_EMAIL_HOST_USER'):
            self.WEATHER_EMAIL_HOST_USER = settings.WEATHER_EMAIL_HOST_USER
        if hasattr(settings, 'WEATHER_EMAIL_HOST_PASSWORD'):
            self.WEATHER_EMAIL_HOST_PASSWORD = settings.WEATHER_EMAIL_HOST_PASSWORD

        from .models import HazardFeeds, EmailActivationCode
        from .signals import send_hazard_feed_notification, send_activation_mail
        post_save.connect(send_hazard_feed_notification, sender=HazardFeeds)
        post_save.connect(send_activation_mail, sender=EmailActivationCode)
        from . import jobs

        try:
            scheduler = django_rq.get_scheduler('default')
            for job in scheduler.get_jobs():
                if job.func_name == 'hazard_feed.jobs.parse_feeds':
                    job.delete()
            scheduler.schedule(scheduled_time=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
                               func=jobs.parse_feeds,
                               interval=600, result_ttl=100
                               )
        except ConnectionError:
            pass