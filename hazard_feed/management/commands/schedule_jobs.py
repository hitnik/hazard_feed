from django.core.management.base import BaseCommand
import django_rq
from rq import Queue
from redis import Redis
import datetime
from rq_scheduler import Scheduler


redis_conn = Redis('default')
q = Queue(connection=redis_conn)
# queue = django_rq.get_queue('default')
scheduler = Scheduler(queue=q)

def clear_scheduled_jobs():
    # Delete any existing jobs in the scheduler when the app starts up
    for job in scheduler.get_jobs():
        job.delete()

def register_scheduled_jobs():
    # do your scheduling here
    scheduler.schedule(scheduled_time=datetime.datetime.utcnow() + datetime.timedelta(minutes=2),
                           func='hazard_feed.jobs.parse_feeds',
                           interval=60*20)


class Command(BaseCommand):

    def handle(self, *args, **options):
        clear_scheduled_jobs()
        register_scheduled_jobs()

