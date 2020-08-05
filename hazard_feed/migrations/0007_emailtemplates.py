# Generated by Django 3.0.2 on 2020-02-06 04:40

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('hazard_feed', '0006_weatherrecipients_uuid'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(editable=False, max_length=64, unique=True)),
                ('template', tinymce.models.HTMLField(null=True)),
            ],
            options={
                'verbose_name': 'Email Template',
                'verbose_name_plural': 'Email Templates',
            },
        ),
    ]
