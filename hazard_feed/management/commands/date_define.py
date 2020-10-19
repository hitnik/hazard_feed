from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import HazardFeeds
from ...utils import date_from_text_parser


def date_define():
    queryset = HazardFeeds.objects.all()
    for item in queryset:
        item.date_start, item.date_end = date_from_text_parser(settings.DATE_API, item.summary)
        print(item.date_start)
        item.save()

class Command(BaseCommand):

    def handle(self, *args, **options):
        date_define()