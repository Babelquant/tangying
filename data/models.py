from django.db import models
from datetime import *
from django.utils import timezone

# Create tangying data here.

class HotStock(models.Model):
    name = models.CharField('股票名',max_length=8)
    rank = models.SmallIntegerField('排名')
    change = models.SmallIntegerField('排名变化')
    concept = models.CharField('概念',max_length=32)
    popularity = models.FloatField('人气')
    express = models.CharField('表现',max_length=16,null=True)
    time = models.DateTimeField('时间',auto_now=True)

    class Meta:
        db_table = 'hotstock'

class LimitupStock(models.Model):
    code = models.CharField('股票代码',max_length=8)
    name = models.CharField('股票名',max_length=8)
    latest = models.FloatField('涨停价')
    currency_value = models.FloatField('流通市值')
    reason_type = models.CharField('涨停原因',max_length=128,null=True)
    limit_up_type = models.CharField('涨停形态',max_length=8)
    high_days = models.CharField('几天几板',max_length=8,null=True)
    change_rate = models.FloatField('换手率',null=True)
    change_tag = models.CharField('换手形态',max_length=32,null=True)
    first_limit_up_time = models.CharField(null=True,max_length=32)
    last_limit_up_time = models.CharField(null=True,max_length=32)
    is_open = models.IntegerField(default=0)
    is_open = models.IntegerField(default=0)
    is_new = models.IntegerField(null=True)
    is_again_limit = models.IntegerField('封板次数',null=True)
    order_amount = models.FloatField('封单额',null=True)
    time_preview = models.TextField(blank=True,default='[]')
    date = models.DateField()

    class Meta:
        db_table = 'limitupstock'
        get_latest_by = 'date'
        
class Security(models.Model):
    code = models.CharField('股票代码',max_length=16)
    srcSecurityCode = models.CharField('证券代码',max_length=16)
    value = models.CharField('中文名称',max_length=8)
    latest = models.FloatField(null=True)
    currency_value = models.FloatField(null=True)
    sixty_days_increase = models.FloatField(null=True)
    year_increase = models.FloatField(null=True)

    class Meta:
        db_table = 'security'

class ConceptStock(models.Model):
    name = models.CharField('股票名称',max_length=8)
    code = models.CharField('股票代码',max_length=16)
    concept = models.CharField('概念',max_length=32)
    latest = models.FloatField('最新价')
    weekly_increase = models.CharField('近1周涨幅',max_length=8)

    class Meta:
        db_table = 'conceptstock'

class Concept(models.Model):
    code = models.CharField('概念板块代码',max_length=16)
    name = models.CharField('概念板块名称',max_length=8)

    class Meta:
        db_table = 'concept'
        
class StockRealtimeRank(models.Model):
    srcSecurityCode = models.CharField(max_length=16)
    rank = models.IntegerField(null=True,default='null')
    time = models.DateTimeField()

    class Meta:
        db_table = 'stockrealtimerank'     

class StockZY(models.Model):
    code = models.CharField(max_length=16)
    zyyw = models.TextField(null=True,default='null')
    jyfw = models.TextField(null=True,default='null')

    class Meta:
        db_table = 'stockzy'  
        
class BidPrice(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField('股票名称',max_length=8)
    latest = models.FloatField('最新价',null=True)
    currency_value = models.FloatField('流通市值')
    increase = models.FloatField(null=True)
    acceleration = models.FloatField('涨速',null=True)
    sixty_days_increase = models.FloatField(null=True)
    year_increase = models.FloatField(null=True)
    time_increase = models.TextField(blank=True,default='[]')
    # time_volume = models.TextField(blank=True,default='[]')
    date = models.DateField()

    class Meta:
        get_latest_by = 'date'
        db_table = 'bidprice'