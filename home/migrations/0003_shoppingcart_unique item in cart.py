# Generated by Django 3.2 on 2021-04-21 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_auto_20210421_1356'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='shoppingcart',
            constraint=models.UniqueConstraint(fields=('username', 'isbn'), name='unique item in cart'),
        ),
    ]