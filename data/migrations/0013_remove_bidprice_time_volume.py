# Generated by Django 4.0.6 on 2023-09-11 22:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_alter_bidprice_options_alter_bidprice_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bidprice',
            name='time_volume',
        ),
    ]
