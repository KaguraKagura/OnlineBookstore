# Generated by Django 3.2 on 2021-04-29 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_auto_20210426_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='usefulness_score',
            field=models.FloatField(default=0.0),
        ),
    ]
