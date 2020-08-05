import re
import feedparser
import time
import datetime
import pytz
from .models import (
    HazardLevels, HazardFeeds,
    WeatherRecipients, EmailTemplates,
    RSSFeedUrl
)
from django.conf import settings
import aiosmtplib
from django.template import loader
from email.message import EmailMessage
from bs4 import BeautifulSoup
from django.apps import apps
from django.template import Context, Template
from django.db.utils import OperationalError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .config import WEATHER_FEED_URL
from django.contrib.sessions.models import Session

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


def create_rss_urls_list():
    urls = list(RSSFeedUrl.objects.filter(is_active=True).values_list('url', flat=True))
    if len(urls) == 0:
        urls.append(WEATHER_FEED_URL)
    return urls


def parse_weather_feeds(*args):
    """
    parse weather hazard rss to django model
    :param url:url of weather page
    :return:
    """
    validator = URLValidator()
    feeds_out = []
    for entry in args:
        if isinstance(entry, str):
            try:
                validator(entry)
                url = entry
                feeds = feedparser.parse(url)
                for feed in feeds.entries:
                    ms = int(time.mktime(feed.published_parsed))
                    date = datetime.datetime.fromtimestamp(ms).replace(tzinfo=pytz.utc)
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
            except ValidationError as e:
                print(e)
                print('--'+entry+'--  not a url')

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
    msg = Message()
    msg['From'] = settings.WEATHER_EMAIL_FROM
    msg['Subject'] = feed.title
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')
    return msg



def get_weather_recipients():
    return list(WeatherRecipients.objects.filter(is_active=True).values_list('email', flat=True))


async def send_mail(msg, recipients):

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



def get_session_obj(request):
    """
    function return django session objects from request
    :param request:
    :return:
    """
    request.session.save()
    session_id = request.session.session_key
    return Session.objects.get(session_key=session_id)

class Message():

    def __init__(self):
        self.activation_template = Template(EmailTemplates.objects.get(title='activation_code_mail').template)
        self.deactivation_template = Template(EmailTemplates.objects.get(title='deactivation_code_mail').template)

    @classmethod
    def email_weather_hazard(cls, feed):
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

    def _email_code(self, code, activate=True):
        if activate:
            template = self.activation_template
        else:
            template = self.deactivation_template
        context = Context({'code': code})
        html = template.render(context)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        msg = EmailMessage()
        msg['From'] = settings.WEATHER_EMAIL_FROM
        if activate:
            msg['Subject'] = 'Код активации подписки'
        else:
            msg['Subject'] = 'Код деактивации подписки'
        msg.set_content(text)
        msg.add_alternative(html, subtype='html')
        return msg


    @classmethod
    def email_activation_code(cls, code):
        return cls()._email_code(code, activate=True)

    @classmethod
    def email_deactivation_code(cls, code):
        return cls()._email_code(code, activate=False)
