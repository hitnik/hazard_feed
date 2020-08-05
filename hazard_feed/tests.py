from django.test import TestCase, override_settings
from .utils import *
from .config import WEATHER_FEED_URL
from django.apps import apps
import asyncio
import django_rq
from rq_scheduler import Scheduler
from .jobs import parse_feeds
from .models import WeatherRecipients
from  django.urls import reverse
from rest_framework.test import APIRequestFactory
from .views import *
from rest_framework.test import APITestCase

class TestHazardFeeds(TestCase):
    fixtures = ['hazard_feed/fixtures/hazard_levels.json']

    def setUp(self):
        pass

    def test_put_feed_to_db(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        self.assertFalse(put_feed_to_db(feeds[0]))
        if len(feeds) > 1:
            self.assertTrue(put_feed_to_db(feeds[1]))

    def test_date_compare(self):
        d1 = datetime.datetime.utcnow()
        d2 = datetime.datetime.utcnow()+datetime.timedelta(hours=3)
        d3 = datetime.datetime.utcnow()+datetime.timedelta(days=1)
        # self.assertEqual(d1.date(), d2.date())
        self.assertNotEqual(d1.date(), d3.date())


    def test_send_weather_mail(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        msg = make_weather_hazard_message(feeds[0])
        recipients = get_weather_recipients()
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(send_mail(msg, recipients))

    def test_rq(self):
        # queue = django_rq.get_queue('default')
        # queue.enqueue(parse_feeds)
        redis_conn = django_rq.get_connection
        scheduler = Scheduler(connection=redis_conn)
        scheduler.schedule(scheduled_time=datetime.datetime.utcnow()+datetime.timedelta(seconds=5),
                               func=parse_feeds,
                               interval=60
                               )
    def test_notify_signal(self):
        feed = HazardFeeds.objects.create(
            id=1580800025,
            date=datetime.datetime.utcnow(),
            date_modified=datetime.datetime.utcnow()+datetime.timedelta(minutes=5),
            title='Предупреждение о неблагоприятном явлении',
            link='http://www.pogoda.by/news/?page=34647',
            summary='Желтый уровень опасности. 5 февраля (среда) на '
                    'отдельных участках дорог республики ожидается гололедица.',
            hazard_level=HazardLevels.objects.get(id=3),
            is_sent=False
        )
        self.assertTrue(feed.is_sent)
        print(feed.date_created)
        print(feed.date_modified)

    def test_recipient(self):
        self.assertIsInstance(get_weather_recipients(), list)

    def test_templated_msg(self):
        feed = HazardFeeds(
            id=1580800025,
            date=datetime.datetime.utcnow(),
            date_modified=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            title='Предупреждение о неблагоприятном явлении',
            link='http://www.pogoda.by/news/?page=34647',
            summary='Желтый уровень опасности. 5 февраля (среда) на '
                    'отдельных участках дорог республики ожидается гололедица.',
            hazard_level=HazardLevels.objects.get(id=3),
            is_sent=False
        )
        feed.save()


    def test_url_not_rss(self):
       print(len(parse_weather_feeds('sfsdf','http://tut.by')))


    def test_parse(self):
        list = create_rss_urls_list()
        print(list)
        feeds = parse_weather_feeds(*list)
        print(feeds)


class TestAPI(APITestCase):

    def test_subscribe(self):
        resp = self.client.post(reverse('hazard_feed:subscribe_newsletter'),
                                {'title': 'test', 'email':'hitnik@gmail.com'},
                                format='json')
        self.assertEqual(resp.status_code, 201)
        print(resp)
        resp = self.client.post(reverse('hazard_feed:subscribe_newsletter'),
                                {'title': 'test', 'email': 'hitnik@gmail.com'},
                                format='json')
        # self.assertEqual(resp.status_code, 201)
        print(resp.content)


    def test_code_gen(self):
        resp = self.client.post(reverse('hazard_feed:activate_subscribe'),
                                {"code": "12345678"}, format='json')
        print(resp.content)