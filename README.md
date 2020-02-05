=====
Hazard_feed
=====

Hazard_feed is a Django app to get storm warnings from http://www.pogoda.by conduct Web-based polls and send notifications 
by email to subscribed recipents.



Quick start
-----------

1. Add "hazard_feed" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'hazard_feed',
    ]

2. Define next email settings in settings.py or your environment viriables:
	        WEATHER_EMAIL_SMTP_HOST
			WEATHER_EMAIL_SMTP_PORT
            WEATHER_USE_TSL
            WEATHER_EMAIL_HOST_USER 
			WEATHER_EMAIL_HOST_PASSWORD
			
3. Define in settings.py
			WEATHER_EMAIL_FROM
			
4. Define django_rq settings

5. Start rqworker and rqscheduler			

4. Run `python manage.py migrate` to create the azard_feed models.