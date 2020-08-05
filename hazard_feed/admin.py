from django.contrib import admin
from .models import (
    HazardLevels, HazardFeeds,
    WeatherRecipients, EmailTemplates,
    RSSFeedUrl, EmailActivationCode
)

class BaseEnadledDisabledModelAdmin(admin.ModelAdmin):
    def make_enabled(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = "1 запись активирована"
        else:
            message_bit = "%s записей были активированы" % rows_updated
        self.message_user(request, "%s" % message_bit)

    make_enabled.short_description = "Сделать активными"

    def make_disabled(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated == 1:
            message_bit = "1 запись отключена"
        else:
            message_bit = "%s записей были отключены" % rows_updated
        self.message_user(request, "%s" % message_bit)

    make_disabled.short_description = "Отключить"

    actions = [make_enabled, make_disabled]




@admin.register(HazardLevels)
class HazardLevelsAdmin(admin.ModelAdmin):
    pass

@admin.register(HazardFeeds)
class HazardFeedsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in HazardFeeds._meta.get_fields()]

@admin.register(WeatherRecipients)
class WeatherRecipientsAdmin(BaseEnadledDisabledModelAdmin):
    list_display = ('title', 'email', 'is_active',)
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    readonly_fields = ('id',)
    ordering = ['id']

@admin.register(EmailTemplates)
class EmailTemplateAdmin(admin.ModelAdmin):
    readonly_fields = (['title'])

@admin.register(RSSFeedUrl)
class RSSFeedUrlAdmin(BaseEnadledDisabledModelAdmin):
    list_display = ('title', 'url', 'is_active',)
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    readonly_fields = ('id',)
    ordering = ['id']

@admin.register(EmailActivationCode)
class EmailActivationCodeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in EmailActivationCode._meta.get_fields()]
    readonly_fields = ('code',)