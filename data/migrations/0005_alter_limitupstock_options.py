# Generated by Django 4.2.2 on 2023-07-05 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_alter_limitupstock_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='limitupstock',
            options={'get_latest_by': 'date'},
        ),
    ]
