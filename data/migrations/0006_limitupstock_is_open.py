# Generated by Django 4.0.6 on 2023-07-23 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_alter_limitupstock_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='limitupstock',
            name='is_open',
            field=models.IntegerField(default=0),
        ),
    ]
