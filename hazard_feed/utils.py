import re
import feedparser
import time
import datetime
import pytz
from .models import (
    HazardLevels, HazardFeeds,
    WeatherRecipients, EmailTemplates
)
from django.conf import settings
import aiosmtplib
from django.template import loader
from email.message import EmailMessage
from bs4 import BeautifulSoup
from django.apps import apps
from django.template import Context, Template
from django.db.utils import OperationalError

def hazard_level_in_text_find(text):
    """
    chek if hazard level in text
    :param text:
    :return:
    """
    try:
        for hazard in HazardLevels.objects.all():
            if re.search(hazard.title, text):
                return hazard
    except OperationalError:
        return None
    return None

def parse_weather_feeds(url):
    """
    parse weather hazard rss to django model
    :param url:url of weather page
    :return:
    """
    feeds = feedparser.parse(url)
    feeds_out = []
    for feed in feeds.entries:
        ms = int(time.mktime(feed.published_parsed))
        date = datetime.datetime.fromtimestamp(ms).replace(tzinfo=pytz.utc)
        # date_parsed = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        hazard_level = hazard_level_in_text_find(feed.summary)
        if hazard_level:
            hazard_feed = HazardFeeds(
                id=feed.id, date=date, title=feed.title,
                link=feed.link, summary=feed.summary,
                hazard_level=hazard_level,
                is_sent=False
            )
            feeds_out.append(hazard_feed)
        else:
            raise Exception('Hazard level define error')
    return feeds_out

def put_feed_to_db(feed):
    try:
        if not HazardFeeds.objects.filter(id=feed.id).exists():
            feed.save()
            return True
    except OperationalError:
        return False
    return False

def make_weather_hazard_message(feed):
    date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    local_tz = pytz.timezone(settings.TIME_ZONE)
    date = date.astimezone(local_tz)
    template = Template(EmailTemplates.objects.get(title='weather_mail').template)
    context = Context({'date': date, 'feed': feed})
    html = template.render(context)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    msg = EmailMessage()
    msg['From'] = settings.WEATHER_EMAIL_FROM
    msg['Subject'] = feed.title
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')
    return msg

def get_weather_recipients():
    return list(WeatherRecipients.objects.filter(is_active=True).values_list('email', flat=True))



async def send_weather_mail(msg, recipients):

    """
    try to get queryset with async
    :param msg:
    :param recipients:
    :return:
    """
    config = apps.get_app_config('hazard_feed')
    if isinstance(recipients, list) and len(recipients) > 0:
        if config.WEATHER_USE_TSL:
            await aiosmtplib.send(
                msg,
                hostname=config.WEATHER_EMAIL_SMTP_HOST,
                port=config.WEATHER_EMAIL_SMTP_PORT,
                use_tls=config.WEATHER_USE_TSL,
                username=config.WEATHER_EMAIL_HOST_USER,
                password=config.WEATHER_EMAIL_HOST_PASSWORD,
                sender=settings.WEATHER_EMAIL_FROM,
                recipients=recipients
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=config.WEATHER_EMAIL_SMTP_HOST,
                port=config.WEATHER_EMAIL_SMTP_PORT,
                username=config.WEATHER_EMAIL_HOST_USER,
                password=config.WEATHER_EMAIL_HOST_PASSWORD,
                sender=settings.WEATHER_EMAIL_FROM,
                recipients=recipients
            )

# def get_weather_mail():
