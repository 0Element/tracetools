# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SeoData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(unique=True, max_length=255, verbose_name='Page url')),
                ('title_tag', models.CharField(max_length=255, verbose_name='Title tag', blank=True)),
                ('meta_description', models.CharField(max_length=255, verbose_name='Meta description', blank=True)),
                ('page_h1', models.CharField(max_length=255, verbose_name='Page h1', blank=True)),
            ],
        ),
    ]
