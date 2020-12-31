from django.test import TestCase
from .utils import *
from .config import WEATHER_FEED_URL
import asyncio
import django_rq
from rq_scheduler import Scheduler
from .jobs import parse_feeds, send_weather_notification
from .models import WeatherRecipients
from django.urls import reverse
from .serializers import ActivationCodeSerializer
import jwt
from rest_framework.test import APITestCase
import datetime
from channels.testing import ChannelsLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random


class TestHazardFeeds(TestCase):
    fixtures = ['hazard_feed/fixtures/hazard_levels.json']

    def setUp(self):
        pass

    def test_put_feed_to_db(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        put_feed_to_db(feeds[0])
        f = HazardFeeds.objects.all()
        for item in f:
            print(item.summary)

            print(item.date_start)
            print(item.date_end)

    def test_date_compare(self):
        d1 = datetime.datetime.utcnow()
        d2 = datetime.datetime.utcnow()+datetime.timedelta(hours=3)
        d3 = datetime.datetime.utcnow()+datetime.timedelta(days=1)
        # self.assertEqual(d1.date(), d2.date())
        self.assertNotEqual(d1.date(), d3.date())


    def test_send_weather_mail(self):

        h1 = HazardLevels.objects.get(id=1)
        h2 = HazardLevels.objects.get(id=2)
        h3 = HazardLevels.objects.get(id=3)
        h4 = HazardLevels.objects.get(id=4)

        feed = HazardFeeds.objects.create(
            id=1580800025,
            date=datetime.datetime.utcnow(),
            date_modified=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            title='Предупреждение о явлении',
            external_link='http://www.pogoda.by/news/?page=34647',
            summary='Желтый уровень опасности. 5 февраля (среда) на '
                    'отдельных участках дорог республики ожидается гололедица.',
            hazard_level=h3,
            is_sent=False
        )

        msg = make_weather_hazard_message(feed)
        recipients = get_weather_recipients(feed)
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
            external_link='http://www.pogoda.by/news/?page=34647',
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
        h1 = HazardLevels.objects.get(id=1)
        h2 = HazardLevels.objects.get(id=2)
        h3 = HazardLevels.objects.get(id=3)
        h4 = HazardLevels.objects.get(id=4)

        feed = HazardFeeds(
            id=1580800025,
            date=datetime.datetime.utcnow(),
            date_modified=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            title='Предупреждение о неблагоприятном явлении',
            external_link='http://www.pogoda.by/news/?page=34647',
            summary='Желтый уровень опасности. 5 февраля (среда) на '
                    'отдельных участках дорог республики ожидается гололедица.',
            hazard_level=HazardLevels.objects.get(id=3),
            is_sent=False
        )
        recipient = WeatherRecipients.objects.create(
            email='',
            title='',
            is_active=True,
        )
        recipient.hazard_levels.set((h2, h3, h4))
        recipient.save()
        feed.save()
        send_weather_notification(feed)

    def test_url_not_rss(self):
       print(len(parse_weather_feeds('sfsdf','http://tut.by')))


    def test_parse(self):
        list = create_rss_urls_list()
        print(list)
        feeds = parse_weather_feeds(*list)
        print(feeds)


class TestApi(APITestCase):


    def test_subscribe(self):
        pass

    def test_subscribe_edit(self):
        h1 = HazardLevels.objects.get(id=1)
        h2 = HazardLevels.objects.get(id=2)
        h3 = HazardLevels.objects.get(id=3)
        h4 = HazardLevels.objects.get(id=4)
        test = WeatherRecipients.objects.create(
            title='test',
            email='test@test.ru',
            is_active=True,
        )
        test.hazard_levels.add(h4)
        resp = self.client.post(reverse('hazard_feed:subscribe_edit'),
                                {'title': 't', 'email': 'test@test.ru', 'hazard_levels': [3, 4]},
                                format='json')
        self.assertEqual(resp.status_code, 200)
        candidate = WeatherRecipientsEditCandidate.objects.get(target__email='test@test.ru')
        self.assertEqual('t', candidate.title)
        resp = self.client.post(reverse('hazard_feed:subscribe_edit'),
                                {'title': 'test', 'email': 'test@test.ru', 'hazard_levels': [3, 4]},
                                format='json')
        self.assertEqual(resp.status_code, 200)
        test.is_active = False
        test.save()
        resp = self.client.post(reverse('hazard_feed:subscribe_edit'),
                                {'title': 'test', 'email': 'tes1t@test.ru', 'hazard_levels': [3, 4]},
                                format='json')
        self.assertEqual(resp.status_code, 404)


    def test_code_gen(self):
        resp = self.client.post(reverse('hazard_feed:activate_subscribe'),
                                {"code": "12345678"}, format='json')
        print(resp.content)


class TestUtils(APITestCase):
    fixtures = ['hazard_levels']

    def test_remove_level(self):
        text = 'Оранжевый уровень опасности. Днем 10 сентября (четверг) на большей части территории республики ожидается усиление ветра порывами до 15-20 м/с.'
        hazard_level = hazard_level_in_text_find(text)
        self.assertEqual(remove_hazard_level_from_feed(hazard_level, text), 'Днем 10 сентября (четверг) на большей части территории республики ожидается усиление ветра порывами до 15-20 м/с.' )

    def text_date_parser(self):
        text = 'Днем 10 сентября (четверг) на большей части территории республики ожидается усиление ветра порывами до 15-20 м/с.'
        date_start, date_end = date_from_text_parser('http://127.0.0.2:5000', text)
        self.assertIsNone(date_start)
        self.assertIsNone(date_end)
        date_start, date_end = date_from_text_parser('http://127.0.0.1:5000/v1/parse-date', text)
        d_s = d_n = datetime.date(2020, 9, 10)
        self.assertEqual(d_s, date_start)
        self.assertEqual(d_n, date_end)


    def test_get_actual_hazard_feeds(self):

        date_yesterday = datetime.datetime.now().date()-datetime.timedelta(days=1)
        date_now = datetime.datetime.now().date()
        date_tommorow = datetime.datetime.now().date()+datetime.timedelta(days=1)

        dates_list = (date_tommorow, date_now, date_yesterday)

        for i in range(1,11):
            index = random.randint(0,2)
            date_start = date_end = dates_list[index]

            if i % 2 == 0 and index < len(dates_list)-1:
                date_end = dates_list[index+1]

            feed = HazardFeeds.objects.create(
                id=i,
                date=datetime.datetime.utcnow(),
                date_modified=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                title='Предупреждение о неблагоприятном явлении',
                external_link='http://www.pogoda.by/news/?page=34647',
                summary=date_start.strftime('%d %b'),
                hazard_level=HazardLevels.objects.get(id=3),
                is_sent=True,
                date_start=date_start,
                date_end=date_end
            )

        feeds = get_actial_hazard_feeds()

        print(len(feeds))

        for feed in feeds:
            self.assertEqual(feed.summary, feed.date_start.strftime('%d %b'))



class TestJWT(APITestCase):

    def test_jwt(self):
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        exp = now + datetime.timedelta(seconds=5)
        token = jwt.encode({'id': '5', 'exp': exp},
                           settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        serializer = ActivationCodeSerializer(data={'code': 12345678, 'token': token })
        serializer.is_valid()
        dict = jwt.decode(serializer.validated_data['token'], settings.SECRET_KEY, algorithm='HS256')
        self.assertEqual('5', dict['id'])


class WSTests(ChannelsLiveServerTestCase):
    serve_static = True  # emulate StaticLiveServerTestCase

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            # NOTE: Requires "chromedriver" binary to be installed in $PATH
            dc = DesiredCapabilities.CHROME
            dc['goog:loggingPrefs'] = {'browser': 'ALL'}

            path = '/usr/local/bin/chromedriver'
            cls.driver = webdriver.Chrome(path, desired_capabilities=dc)
        except:
            super().tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def test_when_ws_group_send(self):
        try:
            h1 = HazardLevels.objects.get(id=1)
            h2 = HazardLevels.objects.get(id=2)
            h3 = HazardLevels.objects.get(id=3)
            h4 = HazardLevels.objects.get(id=4)

            date_now = datetime.datetime.now().date()

            feed = HazardFeeds.objects.create(
                id=1580800025,
                date=datetime.datetime.utcnow(),
                date_modified=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                title='Предупреждение о неблагоприятном явлении',
                external_link='http://www.pogoda.by/news/?page=34647',
                summary=date_now.strftime('%d %b'),
                hazard_level=HazardLevels.objects.get(id=3),
                is_sent=True,
                date_start=date_now,
                date_end=date_now
            )

            recipient = WeatherRecipients.objects.create(
                email='',
                title='',
                is_active=True,
            )

            recipient.hazard_levels.set((h2, h3, h4))
            recipient.save()
            feed.save()


            self._enter_url()

            self._open_new_window()
            self._enter_url()


            self._switch_to_window(0)

            self._post_message('ping')

            WebDriverWait(self.driver, 2).until(lambda _:
                'pong' in self._chat_log_value,
                'Message was not received by window 1 from window 1')



            self._switch_to_window(1)

            self._post_message('feeds')

            WebDriverWait(self.driver, 20).until(lambda _:
                date_now.strftime('%d %b') in self._chat_log_value,
                'Message was not received by window 2 from window 1')

            time.sleep(20)
        finally:
            self._close_all_new_windows()

    # === Utility ===

    def _post_message(self, message):
        ActionChains(self.driver).send_keys(message + '\n').perform()

    def _enter_url(self):
        self.driver.get(self.live_server_url + reverse('hazard_feed:ws_test'))

    def _open_new_window(self):
        self.driver.execute_script('window.open("about:blank", "_blank");')
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def _close_all_new_windows(self):
        while len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.execute_script('window.close();')
        if len(self.driver.window_handles) == 1:
            self.driver.switch_to.window(self.driver.window_handles[0])

    def _switch_to_window(self, window_index):
        self.driver.switch_to.window(self.driver.window_handles[window_index])

    @property
    def _chat_log_value(self):
        return self.driver.find_element_by_css_selector('#chat-log').get_property('value')
