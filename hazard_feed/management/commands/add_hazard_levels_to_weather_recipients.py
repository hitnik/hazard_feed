from django.core.management.base import BaseCommand
from hazard_feed.models import WeatherRecipients, HazardLevels


def add_hazard_levels_to_weather_recipients():
    levels = HazardLevels.objects.all().values_list('id', flat=True)
    queryset = WeatherRecipients.objects.all()
    for item in queryset:
        if not item.hazard_levels.exists():
            item.hazard_levels.add(*levels)
            item.save()

class Command(BaseCommand):

    def handle(self, *args, **options):
        add_hazard_levels_to_weather_recipients()