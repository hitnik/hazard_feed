from django_rq import job
import asyncio
from .utils import (
    parse_weather_feeds, put_feed_to_db,
    send_mail, get_weather_recipients, create_rss_urls_list,
    Message, send_email_async
    )

@job
def parse_feeds():
    urls_list = create_rss_urls_list()
    feeds = parse_weather_feeds(*urls_list)
    for feed in feeds:
        put_feed_to_db(feed)

@job
def send_weather_notification(feed):
    recipients = get_weather_recipients(feed)
    msg = Message.email_weather_hazard(feed)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_mail(msg, recipients))

@job
def send_email_code_activate(code, recipients):
   msg = Message.email_activation_code(code)
   send_email_async(msg, recipients)

@job
def send_email_code_deactivate(code, recipients):
    msg = Message.email_deactivation_code(code)
    send_email_async(msg, recipients)

@job
def send_email_code_edit(code, recipients):
    msg = Message.email_validate_edit_code(code)
    send_email_async(msg, recipients)

