from django_rq import job
from .config import WEATHER_FEED_URL
import asyncio
from hazard_feed.utils import (
    parse_weather_feeds, put_feed_to_db,
    make_weather_hazard_message, send_weather_mail,
    get_weather_recipients
    )

@job
def parse_feeds():
    feeds = parse_weather_feeds(WEATHER_FEED_URL)
    for feed in feeds:
        put_feed_to_db(feed)


@job
def send_notification(feed):
    recipients = get_weather_recipients()
    msg = make_weather_hazard_message(feed)
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(send_weather_mail(msg, recipients))