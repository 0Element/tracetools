# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seodata',
            name='url',
            field=models.CharField(max_length=255, verbose_name='Page url'),
        ),
    ]
