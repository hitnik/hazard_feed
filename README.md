=====
Hazard_feed
=====

Hazard_feed is a Django app to get storm warnings from http://www.pogoda.by conduct Web-based polls and send notifications 
by email to subscribed recipents.



Quick start
-----------

1. Add "hazard_feed", "corsheaders' and others to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'corsheaders',
        'django_rq',
        'tinymce',
        'rest_framework',
        'drf_yasg',
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
			
4. Add "corsheaders' settings to your settings.py 

     CORS_ORIGIN_ALLOW_ALL = True

			
5. Define django_rq settings

6. Start rqworker and rqscheduler

7. For websocket works add channels redis and configure 
it as channels documentation 		

7. Run `python manage.py migrate` to create the azard_feed models.
