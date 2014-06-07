# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0018_eventhousing_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='person',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id'),
            preserve_default=True,
        ),
    ]