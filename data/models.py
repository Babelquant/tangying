from django.db import models

# Create tangying data here.

class HotStocks(models.Model):
    Name = models.CharField('股票名',max_length=8)
    Rank = models.SmallIntegerField('排名')
    Change = models.SmallIntegerField('排名变化')
    Concept = models.CharField('概念',max_length=32)
    Popularity = models.FloatField('人气')
    Express = models.CharField('表现',max_length=16,null=True)
    Time = models.DateTimeField('时间',auto_now=True)

    class Meta:
        db_table = 'hotstocks'

class LimitupStocks(models.Model):
    Name = models.CharField('股票名',max_length=8)
    Code = models.CharField('股票代码',max_length=8)
    # Industry = models.CharField('申万行业',max_length=8,null=True)
    Latest = models.FloatField('涨停价')
    Currency_value = models.IntegerField('流通值')
    Reason_type = models.CharField('涨停原因',max_length=32)
    Limitup_type = models.CharField('涨停形态',max_length=8)
    High_days = models.CharField('几天几板',max_length=8,null=True)
    Change_rate = models.CharField('换手率',max_length=8)
    Date = models.DateTimeField('日期',auto_now=True)

    class Meta:
        db_table = 'limitupstocks'

class Securities(models.Model):
    code = models.CharField('股票代码',max_length=16)
    value = models.CharField('中文名称',max_length=8)
    # name_v = models.CharField('缩写简称',max_length=8)

    class Meta:
        db_table = 'securities'

class ConceptStretagy(models.Model):
    name = models.CharField('股票名称',max_length=8)
    code = models.CharField('股票代码',max_length=16)
    concept = models.CharField('概念',max_length=32)
    last_price = models.FloatField('最新价')
    increase = models.CharField('近1周涨幅',max_length=8)

    class Meta:
        db_table = 'conceptstretagy'

class Concepts(models.Model):
    code = models.CharField('概念板块代码',max_length=16)
    name = models.CharField('概念板块名称',max_length=8)
    # name_v = models.CharField('缩写简称',max_length=8)

    class Meta:
        db_table = 'concepts'