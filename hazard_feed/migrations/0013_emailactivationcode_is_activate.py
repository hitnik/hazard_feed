# Generated by Django 3.0.2 on 2020-04-04 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hazard_feed', '0012_auto_20200322_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailactivationcode',
            name='is_activate',
            field=models.BooleanField(default=True),
        ),
    ]