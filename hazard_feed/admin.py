from django.contrib import admin
from .models import (
    HazardLevels, HazardFeeds,
    WeatherRecipients, EmailTemplates
)

@admin.register(HazardLevels)
class HazardLevelsAdmin(admin.ModelAdmin):
    pass

@admin.register(HazardFeeds)
class HazardFeedsAdmin(admin.ModelAdmin):
    pass

@admin.register(WeatherRecipients)
class WeatherRecipientsAdmin(admin.ModelAdmin):
    pass

@admin.register(EmailTemplates)
class EmailTemplateAdmin(admin.ModelAdmin):
    readonly_fields = (['title'])

