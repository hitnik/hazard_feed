import datetime
import django_rq
from .jobs import send_weather_notification, send_code_notification
from redis.exceptions import ConnectionError
from django.contrib.auth.hashers import check_password, make_password

def send_hazard_feed_notification(sender, instance, created, **kwargs):
    if created \
            and not instance.is_sent and (
                instance.date.date() == instance.date_created.date()
                or instance.is_newer_that(datetime.timedelta(hours=1))
            ):
        try:
            queue = django_rq.get_queue()
            queue.enqueue(send_weather_notification, instance)
            instance.date_send_set()
            instance.is_sent = True
            instance.save()
        except ConnectionError:
            pass


def send_activation_mail(sender, instance, created, **kwargs):
    if created:
        queryset = instance.__class__.objects.filter(target=instance.target)
        for item in queryset:
            if not item == instance:
                item.delete()
        if hasattr(instance.target, 'email'):
            recipients = [instance.target.email]
            code = instance.code
            instance.code = make_password(code)
            queue = django_rq.get_queue()
            queue.enqueue(send_code_notification, code, recipients, activate=instance.is_activate)
            instance.save()
