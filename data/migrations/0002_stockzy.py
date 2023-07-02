# Generated by Django 4.2.2 on 2023-07-02 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockZY',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16)),
                ('zyyw', models.TextField(default='null', null=True)),
                ('jyfw', models.TextField(default='null', null=True)),
            ],
            options={
                'db_table': 'stockzy',
            },
        ),
    ]