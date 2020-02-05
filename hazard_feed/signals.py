import datetime
import django_rq
from .jobs import send_notification

def send_hazard_feed_notification(sender, instance, created, **kwargs):
    if created \
            and not instance.is_sent and (
                instance.date.date() == instance.date_created.date()
                or instance.is_newer_that(datetime.timedelta(hours=1))
            ):
        queue = django_rq.get_queue()
        queue.enqueue(send_notification, instance)
        instance.date_send_set()
        instance.is_sent = True
        instance.save()
