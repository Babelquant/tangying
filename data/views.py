from django.shortcuts import render
from data.models import *
from data.serializers import *
import pandas as pd
import json
from collections import Counter 
import time as tm
import asyncio
import aiohttp
from asgiref.sync import sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from datetime import *
from chinese_calendar import is_workday
import numpy as np
import akshare as ak
from data.cron import *
from django.http import HttpResponse
from django.db.models import Aggregate,CharField,Count,F

# from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

#交易日判断
def is_trade_day(date):
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False

#获取前n个交易日的日期
def beforDaysn(date: str,n: int):
    if n<0:
        return 
    d = datetime.strptime(date,'%Y%m%d')
    i=0
    while i<n:
        d= d-timedelta(days=1)
        if is_trade_day(d):
            i+=1
    return d.strftime('%Y%m%d')
        

#自定义数据库API
class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s separator "+")'

    def __init__(self, expression, distinct=False, separator='+', **extra):
        super(GroupConcat, self).__init__(  #python中super用于子类重写父类方法
            expression,
            distinct='DISTINCT ' if distinct else '',
            # separator=' separator "%s"' % separator,
            output_field=CharField(),
            **extra)

class HotStockViewSet(APIView):  
    permission_classes = [AllowAny]
    # pagination_class = DataPagination
    filterset_fields = ['asin', 'shop', 'brand', 'festival', 'carrier']

    #不分页
    def get(self,request):
        query_params = request.query_params
        # 使用过滤器过滤数据
        queryset = HotStock.objects.order_by('id')
        # Filter queryset based on query parameters in the request  
        for key in query_params:
            if key in self.filterset_fields:
                if query_params[key] is not None and query_params[key] != '':
                    # if key == 'kind':
                    #     queryset = queryset.filter(kind__contains=query_params[key])
                    # else:
                    queryset = queryset.filter(**{key: query_params[key]})
        # Serialize the paginated queryset and return it to the client
        res = HotStockSerializer(queryset, many=True)
        # return paginator.get_paginated_response(res.data)
        return Response({
            # rest_framework.response.Response转dict
            "data": res.data,
            "code": 200,
            "message": "请求成功"
        })

class LimitupStockViewSet(APIView):  
    permission_classes = [AllowAny]
    filterset_fields = ['high_days']

    #不分页
    def get(self,request):
        query_params = request.query_params
        if 'date' in query_params:
            date = datetime.strptime(query_params['date'], "%Y-%m-%d")
            #判断日期是否为交易日
            while True:
                if is_trade_day(date):
                    break
                date = date - timedelta(days=1)
            
            queryset = LimitupStock.objects.filter(date=date.strftime("%Y-%m-%d"))
        else:
            queryset = LimitupStock.objects.order_by('id')

        # Filter queryset based on query parameters in the request  
        for key in query_params:
            if key in self.filterset_fields:
                if query_params[key] is not None and query_params[key] != '':
                    if key == "high_days":
                        queryset = LimitupStock.objects.filter(high_days__in=query_params.getlist('high_days'))
                    else:
                        queryset = queryset.filter(**{key: query_params[key]})

        #判断是否有数据
        # if not queryset.exists():

        # Serialize the paginated queryset and return it to the client
        res = LimitupStockSerializer(queryset, many=True)
        # return paginator.get_paginated_response(res.data)
        return Response({
            # rest_framework.response.Response转dict
            "data": res.data,
            "code": 200,
            "message": "请求成功"
        })
        
class AbnormalStockRankViewSet(APIView):
    permission_classes = [AllowAny]
    
    def get(self,request):
    #     query_params = request.query_params
    #     if 'date' in query_params:
    #         rows = []
    #         date = datetime.strptime(query_params['date'], "%Y-%m-%d")
    #         last_date = date - timedelta(days=1)
            
    #         stocks = Security.objects.all()
    #         for stock in stocks:
    #             qs = StockRealtimeRank.objects.filter(srcSecurityCode=stock.srcSecurityCode,time__date__in=[last_date,date]).aggregate(
    #                 max_rank=models.Max('rank'), min_rank=models.Min('rank'))
    #             row = model_to_dict(stock)
    #             if not row['latest']:
    #                 continue
    #             try:
    #                 row['rank_change'] = qs['max_rank'] - qs['min_rank']
    #             except:
    #                 row['rank_change'] = 0
    #             rows.append(row)

    #         sorted_rows = sorted([row for row in rows if row['rank_change'] > 500 and row['latest'] < 30], key=lambda x: x['rank_change'], reverse=True)
    #         return Response({
    #             "data": sorted_rows[:100],
    #             "code": 200,
    #             "message": "请求成功"
    #         })
    
        stock_hot_up_em_df = ak.stock_hot_up_em()
        stock_hot_up_em_df = stock_hot_up_em_df.drop('涨跌额',axis=1)
        stock_hot_up_em_df.rename(columns={'排名较昨日变动':'rank_change','当前排名':'rank','代码':'sym','股票名称':'name','最新价':'latest','涨跌幅':'increase'},inplace=True)
        rows = []
        for _,row in stock_hot_up_em_df.iterrows():
            try:
                security = Security.objects.get(srcSecurityCode=row.sym.lower())
            except:
                print(f"{row.sym} does not exist.")
                continue
            row = row.to_dict()
            row['code'] = security.code
            row['currency_value'] = security.currency_value
            row['sixty_days_increase'] = security.sixty_days_increase
            row['year_increase'] = security.year_increase
            rows.append(row)
        return Response({
            "data": rows,
            "code": 200,
            "message": "请求成功"
        })   

class LimitupContinueViewSet(APIView):  
    permission_classes = [AllowAny]

    #不分页
    def get(self,request):
        query_params = request.query_params
        if 'date' in query_params:
            date = datetime.strptime(query_params['date'], "%Y-%m-%d")
            #判断日期是否为交易日
            while True:
                if is_trade_day(date):
                    break
                date = date - timedelta(days=1)
            today_date = date
            queryset_today = LimitupStock.objects.filter(date=date.strftime("%Y-%m-%d"),high_days__in=['2天2板'],is_open=0)
            while True:
                date = date - timedelta(days=1)
                if is_trade_day(date):
                    break
            yeastoday_date = date
            queryset_yeastoday = LimitupStock.objects.filter(date=date.strftime("%Y-%m-%d"),high_days__in=['首板'],is_open=0)

            win2TodayData = LimitupStockSerializer(queryset_today, many=True).data
            yeastodayData1 = LimitupStockSerializer(queryset_yeastoday, many=True).data

            #1进2晋级票昨日数据
            win2Data = [d for d in yeastodayData1 if d['code'] in [item['code'] for item in win2TodayData]]
            # for win in win2Data:
            #     df = ak.stock_zh_a_hist(symbol=win['code'], period="daily", start_date=yeastoday_date.strftime("%Y%m%d"), end_date=yeastoday_date.strftime("%Y%m%d"), adjust="qfq")
            #     win['success'] = 1
            #     win['increase'] = df.loc[0,'涨跌幅']
            #     win['swing'] = df.loc[0,'振幅']
            #     win['change_rate'] = df.loc[0,'换手率']
            #1进2晋级票今日数据
            for win in win2TodayData:
                df = ak.stock_zh_a_hist(symbol=win['code'], period="daily", start_date=today_date.strftime("%Y%m%d"), end_date=today_date.strftime("%Y%m%d"), adjust="qfq")
                win['success'] = 1
                v = [item for item in win2Data if item['code'] == win['code']][0]
                win['last_time_preview'] = v['time_preview']
                win['open'] = round((df.loc[0,'开盘'] - v['latest'])/v['latest']*100,1)
                win['increase'] = df.loc[0,'涨跌幅']
                win['swing'] = df.loc[0,'振幅']
                win['change_rate'] = df.loc[0,'换手率']
            
            #1进2淘汰
            out2TodayData = []
            out2Data = [d for d in yeastodayData1 if d['code'] not in [item['code'] for item in win2TodayData]]
            for out in out2Data:
                df = ak.stock_zh_a_hist(symbol=out['code'], period="daily", start_date=yeastoday_date.strftime("%Y%m%d"), end_date=today_date.strftime("%Y%m%d"), adjust="qfq")
                out['success'] = 0
                out['increase'] = df.loc[0,'涨跌幅']
                out['swing'] = df.loc[0,'振幅']
                out['change_rate'] = df.loc[0,'换手率']
                out2TodayData.append({
                    'code': out['code'],
                    'name': out['name'],
                    'currency_value': out['currency_value'],
                    'reason_type': out['reason_type'],
                    'limit_up_type': out['limit_up_type'],
                    'last_time_preview': out['time_preview'],
                    'first_limit_up_time': '',
                    'last_limit_up_time': '',
                    'order_amount': None,
                    'date': today_date,
                    'success': 0,
                    'open': round((df.loc[1,'开盘'] - out['latest'])/out['latest']*100,1),
                    'latest': df.loc[1,'收盘'],
                    'increase': df.loc[1,'涨跌幅'],
                    'swing': df.loc[1,'振幅'],
                    'change_rate': df.loc[1,'换手率']
                })

            queryset_today = LimitupStock.objects.filter(date=today_date.strftime("%Y-%m-%d"),high_days__in=['3天3板'],is_open=0)
            queryset_yeastoday = LimitupStock.objects.filter(date=yeastoday_date.strftime("%Y-%m-%d"),high_days__in=['2天2板'],is_open=0)
            win3TodayData = LimitupStockSerializer(queryset_today, many=True).data
            yeastodayData2 = LimitupStockSerializer(queryset_yeastoday, many=True).data

            #2进3晋级
            win3Data = [d for d in yeastodayData2 if d['code'] in [item['code'] for item in win3TodayData]]
            # for win in win3Data:
            #     df = ak.stock_zh_a_hist(symbol=win['code'], period="daily", start_date=yeastoday_date.strftime("%Y%m%d"), end_date=yeastoday_date.strftime("%Y%m%d"), adjust="qfq")
            #     win['success'] = 1
            #     win['increase'] = df.loc[0,'涨跌幅']
            #     win['swing'] = df.loc[0,'振幅']
            #     win['change_rate'] = df.loc[0,'换手率']
            for win in win3TodayData:
                df = ak.stock_zh_a_hist(symbol=win['code'], period="daily", start_date=today_date.strftime("%Y%m%d"), end_date=today_date.strftime("%Y%m%d"), adjust="qfq")
                win['success'] = 1
                v = [item for item in win3Data if item['code'] == win['code']][0]
                win['last_time_preview'] = v['time_preview']
                win['open'] = round((df.loc[0,'开盘'] - v['latest'])/v['latest']*100,1)
                win['increase'] = df.loc[0,'涨跌幅']
                win['swing'] = df.loc[0,'振幅']
                win['change_rate'] = df.loc[0,'换手率']
            
            #2进3淘汰
            out3TodayData = []
            out3Data = [d for d in yeastodayData2 if d['code'] not in [item['code'] for item in win3TodayData]]
            for out in out3Data:
                df = ak.stock_zh_a_hist(symbol=out['code'], period="daily", start_date=yeastoday_date.strftime("%Y%m%d"), end_date=today_date.strftime("%Y%m%d"), adjust="qfq")
                out['success'] = 0
                out['increase'] = df.loc[0,'涨跌幅']
                out['swing'] = df.loc[0,'振幅']
                out['change_rate'] = df.loc[0,'换手率']
                out3TodayData.append({
                    'code': out['code'],
                    'name': out['name'],
                    'currency_value': out['currency_value'],
                    'reason_type': out['reason_type'],
                    'limit_up_type': out['limit_up_type'],
                    'last_time_preview': out['time_preview'],
                    'first_limit_up_time': '',
                    'last_limit_up_time': '',
                    'order_amount': None,
                    'date': today_date,
                    'success': 0,
                    'open': round((df.loc[1,'开盘'] - out['latest'])/out['latest']*100,1),
                    'latest': df.loc[1,'收盘'],
                    'increase': df.loc[1,'涨跌幅'],
                    'swing': df.loc[1,'振幅'],
                    'change_rate': df.loc[1,'换手率']
                })

            yeastodayData = yeastodayData1 + yeastodayData2
            todayData2 = win2TodayData + out2TodayData
            todayData3 = win3TodayData + out3TodayData
            return Response({
                "data": {'yeastoday_data': yeastodayData, 'today_data2': todayData2, 'today_data3': todayData3},
                "code": 200,
                "message": "请求成功"
            })

class ConceptHotViewSet(APIView):  
    permission_classes = [AllowAny]

    #不分页
    def get(self,request):
        rowData = [('Date','Concept','LimitUpNum')]
        # result = LimitupStock.objects.values('date').annotate(reason_types=Concat('reason_type', Value('+'), output_field=CharField()))
        result = LimitupStock.objects.values('date').annotate(reason_types=GroupConcat(F('reason_type')))
        for row in result:
            if not row['reason_types']:
                continue
            top10 = Counter(row['reason_types'].split('+')).most_common(10)
            for c,n in top10:
                rowData.append([row['date'],c,n])  
        return Response({
            "data": rowData,
            "code": 200,
            "message": "请求成功"
        })

def getHotRankStocks(request):
    chart = [('Name','Rank','Change','Concept','Popularity','Express','Time')]
    # try:
    #原生sql查询
    # engine = getSqliteEngine()
    # print(engine.execute("SELECT * FROM hotstocks").fetchall())  
    #ORM查询
    hotstocks = HotStock.objects.filter(Time__gte=datetime.today()-timedelta(days=1)).\
    values_list('Name','Rank','Change','Concept','Popularity','Express','Time')
    # for hotstock in hotstocks:
    #     print(hotstock[-1])
    for hotstock in hotstocks:
        chart.append(hotstock)
    # except Exception as e:
    #     print(e)
    
    return HttpResponse(json.dumps(chart,cls=DjangoJSONEncoder,ensure_ascii=False))

def getHotTop10Stocks(request):
    top10 = []
    # today = datetime.date(2022,8,2)
    stocks = HotStock.objects.filter(Time__gte=datetime.today()-timedelta(days=1)).filter(Rank__lte=10).values('Name').distinct()
    for stock in stocks:
        top10.append(stock['Name'])
    return HttpResponse(json.dumps(top10,ensure_ascii=False))

#查询最新涨停股
#values做分组
#annotate,aggregate做聚合

#箱体形态模型
#maxdrop:去掉最大值个数
#返回数据：[top,bottom]
def boxPrice(data,maxdrop=0):
    #计算high一介导二阶导
    high_diff1 = data[['high']].diff(periods=1,axis=0).rename(columns={'high':'high_diff1'})
    high_diff2 = data[['high']].diff(periods=2,axis=0).rename(columns={'high':'high_diff2'})
    #计算计算low一介导二阶导
    low_diff1 = data[['low']].diff(periods=1,axis=0).rename(columns={'low':'low_diff1'})
    low_diff2 = data[['low']].diff(periods=2,axis=0).rename(columns={'low':'low_diff2'})
    #合并统计数据
    data = pd.concat([data,high_diff1,high_diff2,low_diff1,low_diff2],axis=1)
    #计算箱体顶部数据集
    high_set = data[(data.high_diff1>0) & (data.high_diff2>0)]
    #计算箱体底部数据集
    low_set = data[(data.low_diff1<0) & (data.low_diff2<0)]

    low_price = low_set[['low']].min()[0]
    # high_price = high_set[['high']].max()[0]
    high_price = high_set.nlargest(maxdrop+1,'high').high.iloc[maxdrop]
    return [high_price,low_price]
    # print("近期最低价:",low_price)

#获取短期快速下跌的票,v型反转
#说明:
#股价低于9元
#流通盘小于80亿
#近5日跌幅超8%
#月内跌幅超18%
#半年跌幅大于月内跌幅1.5倍
#最低价与年内最低价（去掉一个最低价）差价20%以内
def getSharpfallStrategy(request):
    sharpfalls = []
    #获取所有股票
    sh_em_df = ak.stock_sh_a_spot_em()
    sz_em_df = ak.stock_sz_a_spot_em()
    em_df = pd.concat([sh_em_df,sz_em_df]).reset_index(drop=True)
    #筛选
    # first_em_df = em_df[(em_df.最新价<9) & (em_df.流通市值/10**8<80) & (em_df.六十日涨跌幅<-50.0)][['代码','名称','最低','最新价','六十日涨跌幅']]
    first_em_df = em_df[(em_df.最新价<9) & (em_df.流通市值/10**8<80)][['代码','名称','最低','最新价']].reset_index(drop=True)
    # print(first_em_df)
    end = datetime.today().strftime('%Y%m%d')
    for _,row in first_em_df.iterrows():
        code = getattr(row,'代码')
        print(code)
        if code.startswith('300'):
            continue
        last_price = getattr(row,'最新价')
        low_price = getattr(row,'最低')
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=beforDaysn(end,250), end_date=end)
        #近5日跌幅
        five_day_high_price = stock_zh_a_hist_df.tail().reset_index(drop=True).loc[0,'最高']
        five_day_drop_rate = (five_day_high_price-low_price)/five_day_high_price*100
        if five_day_drop_rate < 8:
            continue
        #月内最高价
        a_month_high_price = stock_zh_a_hist_df.tail(25).最高.max()
        #月内跌幅
        a_month_drop_rate = (a_month_high_price-last_price)/a_month_high_price*100
        #近半年最高价
        # print(stock_zh_a_hist_df)
        half_year_high_price = stock_zh_a_hist_df.tail(120).最高.max()
        #半年最高跌幅
        half_year_drop_rate = (half_year_high_price-last_price)/half_year_high_price*100
        #半年跌幅必须大于月内跌幅1.5倍
        if half_year_drop_rate < a_month_drop_rate*1.5:
            continue
        #月内跌幅超18%，5日跌幅超8%,与年内最低点差价10%以内
        if a_month_drop_rate>18:
            stock_individual_info_em_df = ak.stock_individual_info_em(symbol=code)
            #年内最低价，去掉1个最小值
            year_low_price = stock_zh_a_hist_df.nsmallest(2,'最低').最低.iloc[1]
            if year_low_price*0.8 < low_price and year_low_price*1.2 > low_price:
                sharpfall = {
                    '股票': getattr(row,'名称'),
                    '行业': stock_individual_info_em_df.iloc[2,1],
                    '最新价': last_price,
                    '半年最高价': half_year_high_price,
                    '半年最高跌幅': str(round(half_year_drop_rate,1))+'%',
                    '5日跌幅': str(round(five_day_drop_rate,1))+'%', 
                    '月内跌幅': str(round(a_month_drop_rate,1))+'%', 
                }
                sharpfalls.append(sharpfall)
        #     continue
        # if five_day_drop_rate < 15:
        #     continue
        # #最高价时间点
        # index = stock_zh_a_hist_df[stock_zh_a_hist_df.最高==half_year_high_price].index[0]
        # #最高点出现在2个月以前
        # print('index:',index)
        # if index > 80:
        #     continue
        # print(half_year_high_price,five_day_drop_rate,half_year_drop_rate)
        # if half_year_drop_rate < 40.0:
        #     continue
        # #个股信息
        # stock_individual_info_em_df = ak.stock_individual_info_em(symbol=code)
        # sharpfall = {
        #     '股票': getattr(row,'名称'),
        #     '行业': stock_individual_info_em_df.iloc[2,1],
        #     '最新价': last_price,
        #     '半年最高价': half_year_high_price,
        #     '半年最高跌幅': str(round(half_year_drop_rate,1))+'%',
        #     '5日跌幅': str(round(five_day_drop_rate,1))+'%', 
        #     '月内跌幅': str(round(a_month_drop_rate,1))+'%', 
        # }
        # print(sharpfall)
        # sharpfalls.append(sharpfall)
    return HttpResponse(json.dumps(sharpfalls,cls=DjangoJSONEncoder,ensure_ascii=False))

#股票历史排名
class StockHisRankViewSet(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        sym = Security.objects.get(code=request.query_params['code']).srcSecurityCode
        try:
            stock_rank_detail_em_df = ak.stock_hot_rank_detail_em(symbol=sym)
        except Exception as e:
            print(f"获取历史排名失败:{e}")
            return Response({
                "data": str(e),
                "code": 205,
                "message": "请求失败"
            })
        data = {
            'date': stock_rank_detail_em_df['时间'].to_list(),
            'rank': stock_rank_detail_em_df['排名'].to_list()
        }
        return Response({
            "data": data,
            "code": 200,
            "message": "请求成功"
        })

class ConceptData(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Concept.objects.order_by('id')
        res = ConceptSerializer(queryset, many=True)
        return Response({
            "data": res.data,
            "code": 200,
            "message": "请求成功"
        })

#概念策略
# def conceptStockData(request,**kwargs):
class ConceptStockDataViewSet(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query_params = request.GET
        # for concept_code in kwargs['codes'].split(','):
        dfs = []
        for concept_code in query_params['codes'].split(','):
            try:
                stock_board_cons_ths_df = ak.stock_board_cons_ths(symbol=concept_code)
                stock_board_cons_ths_df.drop(columns=['序号','涨跌','涨速','换手','量比','振幅','成交额','流通股','市盈率'],inplace=True)
            except:
                print(concept_code)
                continue
            # concept = Concept.objects.get(code=concept_code).name
            dfs.append(stock_board_cons_ths_df)
        if len(dfs) >= 1:
            merged_df = dfs.pop()
            while(dfs):
                df = dfs.pop()
                merged_df = pd.merge(merged_df,df[['代码']],how="inner",on="代码")
        else:
            return Response({
                # rest_framework.response.Response转dict
                "code": 201,
                "message": "请求失败"
            })

        rows = []
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(conceptWinStocksLoop(merged_df,rows))
        loop.close()

        # df = pd.DataFrame(rows,columns=['Name','Code','Latest','Currency_value','Change_percent','All_rank','Ind_rank','Related_concept'])
        # if not win_stock.empty:
        #     win_stock.insert(loc=4,column='Concept',value=concept)
        #     win_stock_set.append(win_stock)
        #df转dict
        # for concept_stock in np.array(origin_stocks).tolist():
        #     concept_stocks.append({'name':concept_stock[0],'code':concept_stock[1],'concept':concept_stock[4],'last_price':concept_stock[2],'increase':concept_stock[3]})
        # concept_stocks = pd.concat(concept_stocks_dfs).to_dict('records')
        # return HttpResponse(json.dumps(rows,cls=DjangoJSONEncoder,ensure_ascii=False))
        # return HttpResponse(json.dumps(rows,ensure_ascii=False))
        return Response({
            # rest_framework.response.Response转dict
            "data": rows,
            "code": 200,
            "message": "请求成功"
        })
    
#获取概念潜力股筛选数据
async def conceptWinStocks(stock,rows):
    #基础数据
    stock_code = stock.代码
    if stock_code.startswith('300'):
        return
    print(stock.名称)
    #判断是否st
    # if jq.get_extras('is_st',stock,end_date=now,count=1,df=True).iloc[0,0]:
    #     continue
    try:
        #流通值/亿
        if float(stock.流通市值.rstrip('亿')) > 100:
            return
        #涨跌幅
        changepercent = stock.涨跌幅
        latest = float(stock.现价)
    except:
        return
    if latest > 30:
        return

    #最近涨幅
    try:
        stock_inc = await sync_to_async(Security.objects.get)(code=stock_code)
    except:
        return

    #最新排名
    try:
        stock_hot_rank_latest_em_df = ak.stock_hot_rank_latest_em(symbol=stock_inc.srcSecurityCode)
        rank = stock_hot_rank_latest_em_df[stock_hot_rank_latest_em_df.item == "rank"].iloc[-1,-1]
        rank_change = stock_hot_rank_latest_em_df[stock_hot_rank_latest_em_df.item == "rankChange"].iloc[-1,-1]
    except:
        rank = None
        rank_change = None
        
    #主营介绍
    stock_zy = await sync_to_async(StockZY.objects.get)(code=stock_code)

    rows.append({
        'name': stock.名称,
        'code': stock_code,
        'latest':latest,
        'currency_value': stock.流通市值,
        'increase': changepercent,
        'sixty_days_increase': stock_inc.sixty_days_increase,
        'year_increase': stock_inc.year_increase,
        'rank': rank,
        'rank_change': rank_change,
        'zyyw': stock_zy.zyyw,
        'jyfw': stock_zy.jyfw
    })

async def conceptWinStocksLoop(stocks,rows):
    works = []
    #获取概念成份股
    for _,stock in stocks.iterrows():
        works.append(conceptWinStocks(stock,rows))
    await asyncio.gather(*works)

class BidPriceAbnormalViewSet(APIView):
    permission_classes = [AllowAny]
    
    def get(self,request):
        query_params = request.query_params
        if 'date' in query_params:
            date = datetime.strptime(query_params['date'], "%Y-%m-%d")
            #判断日期是否为交易日
            while True:
                if is_trade_day(date):
                    break
                date = date - timedelta(days=1)
            
            queryset = BidPrice.objects.filter(date=date.strftime("%Y-%m-%d"))
        else:
            queryset = BidPrice.objects.latest()
            
        res = BidPriceSerializer(queryset, many=True)
        return Response({
            "data": res.data,
            "code": 200,
            "message": "请求成功"
        })        

#妖股策略
#code:股票代码
#near:统计最近多少个交易日的股价最低点
#ratio:首板价与最近几个月最低价比值范围 
def isMonster(code,nearday=100,ratio=[1,1.5]):
    if code == "":
        return False
    #获取最近100个交易日行情数据df
    price_data_100 = getStockPrice(code).tail(nearday)
    #获取最新最高价
    latest_high = price_data_100[['high']].tail(1).values[0][0]
    #计算最近3个月最低价
    box100 = boxPrice(price_data_100)
    high100 = box100[0]
    low100 = box100[1]
    #获取最近1年行情数据df
    price_data_250 = getStockPrice(code).tail(250)
    box250 = boxPrice(price_data_250,maxdrop=2)
    high250 = box250[0]
    low250 = box250[1]

    #获取最近3年行情数据df
    price_data_800 = getStockPrice(code).tail(800)
    box800 = boxPrice(price_data_800,maxdrop=4)
    high800 = box800[0]
    low800 = box800[1]

    if high800/low800 > 2.5:
        return False

    if high250/low250 > 2:
        return False    

    if latest_high/low100 < ratio[0] or latest_high/low100 > ratio[1]:
        return False

    #当前最新价大于最近3月最高价1.1倍
    if latest_high > high100*1.1:
        return False

    # print('近期最低价：',low100)
    # print('近期最高价：',high100)
    # print('近3年最低价：',low800) 
    # print('近3年最高价：',high800)
    return True

class StockZyViewSet(APIView):
    permission_classes = [AllowAny]
    
    def get(self,request):
        try:
            queryset = StockZY.objects.get(code=request.query_params['code'])
            serializer = StockZYSerializer(queryset)
            return Response({
                "data": serializer.data['zyyw'],
                "code": 200,
                "message": "请求成功"
            })
        except StockZY.DoesNotExist:
            return Response({
                "code": 404,
                "message": "数据不存在"
            })


#首板策略
def firstBoardStrategy(request):
    #所有板块概念
    all_concepts = Concepts.objects.values('name','code')
    #获取当前时刻
    stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
    #获取异动板块
    board_concept_name = stock_board_concept_name_em_df.iloc[0,1]
    print("name:",board_concept_name)
    board_concept = all_concepts.get(name__contains=board_concept_name)
    print('board_code:',board_concept)
    #获取板块概念成分股
    # ths_df = ak.stock_board_cons_ths(symbol=board_concept_code)
    # #涨跌幅在1%内，振幅在2%以内
    # stocks_df = ths_df[(ths_df.涨跌幅<1) & (ths_df.流通市值/10**8<80) & (ths_df.振幅<2)].reset_index(drop=True)
    # return HttpResponse(json.dumps(stocks_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#获取涨停股行业统计数据
def industryStatistic(request):
    chart = [['Industry', 'Limitup_count','Relative_stocks','Date']]
    limitup_stocks_pool = LimitupStocks.objects.filter(Date__month=datetime.now().month).\
    values('Industry').annotate(Limitup_count=Count('Name'),Relative_stocks=GroupConcat('Name')).values_list('Industry', 'Limitup_count','Relative_stocks','Date').order_by('Date')
    for limitup_stock_pool in limitup_stocks_pool:  #返回值类型为元组
        #拿到数据库中时间字符串二次加工以满足图表对时间格式的要求
        list_limitup_stock_pool = list(limitup_stock_pool)
        list_limitup_stock_pool[3] = list_limitup_stock_pool[3].strftime('%Y-%m-%d')
        chart.append(list_limitup_stock_pool)
    return HttpResponse(json.dumps(chart,cls=DjangoJSONEncoder,ensure_ascii=False))

#获取所有股票信息
def getAllSecurities(request):
    all_stocks_name = Securities.objects.values('value','code') 
    #qs数据格式返回字典的列表方法:list
    return HttpResponse(json.dumps(list(all_stocks_name),ensure_ascii=False))

#获取单只股票数据
#返回值：
# 名称	    类型	    描述
# 0.日期	object	    交易日
# 1.开盘	float64	    开盘价
# 2.收盘	float64	    收盘价
# 3.最高	float64	    最高价
# 4.最低	float64	    最低价
# 5.成交量	int32	    注意单位: 手
# 6.成交额	float64	    注意单位: 元
# 7.振幅	float64	    注意单位: %
# 8.涨跌幅	float64	    注意单位: %
# 9.涨跌额	float64	    注意单位: 元
# 10.换手率	float64	    注意单位: %
def getStockPrice(code):
    today = datetime.today().strftime('%Y%m%d')
    candlestick_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20181201", end_date=today, adjust="qfq")
    return candlestick_df.dropna()

#搜索股票历史数据接口
def getCandlestick(request,code):
    candlestick = getStockPrice(code)
    # candlestick_df.rename(columns={'index','date'},inplace=True)
    return HttpResponse(json.dumps(np.array(candlestick).tolist(),cls=DjangoJSONEncoder,ensure_ascii=False))

class StockCandlestick(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params['code']
        today = datetime.today().strftime('%Y%m%d')
        try:
            candlestick_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20181201", end_date=today, adjust="qfq")
            candlestick_df = candlestick_df.dropna()
            sym = Security.objects.get(code=code).srcSecurityCode
            stock_rank_detail_em_df = ak.stock_hot_rank_detail_em(symbol=sym)
            stock_rank_detail_em_df = stock_rank_detail_em_df[['时间','排名']]
            stock_rank_detail_em_df.rename(columns={'时间':'日期'},inplace=True)
            stock_rank_detail_em_df['日期'] = pd.to_datetime(stock_rank_detail_em_df['日期']).dt.date
            candlestick_df['日期'] = pd.to_datetime(candlestick_df['日期']).dt.date
            df = candlestick_df.merge(stock_rank_detail_em_df, how="left", on="日期")
        except Exception as e:
            print(e)
            return Response({
                "data": None,
                "code": 202,
                "error": e,
                "message": "请求失败"
            })
        df['排名'].fillna('-',inplace=True)
        return Response({
            "data": df.values.tolist(),
            "code": 200,
            "message": "请求成功"
        })


#个股实时行情
def getLatestPrice(request,code):
    today = datetime.today().strftime('%Y%m%d')
    price_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=beforDaysn(today,10), end_date=today, adjust="qfq")
    latest_price = price_df.tail(1)
    return HttpResponse(json.dumps(latest_price.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#获取实时资讯
def getNews(request):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    while True:
        try:
            js_news_df = ak.js_news(timestamp=ts)
        except:
            tm.sleep(2)
            continue
        break
    js_news_df.sort_index(ascending=False,inplace=True)
    return HttpResponse(json.dumps(js_news_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#盘口异动数据
#stock_changes_em

#爬取同花顺股票详情页 -----异步io
# async def scrapStockInfo(symbol,stock_info):
#     # stock_info = {}
#     h = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}
#     url_info = 'http://basic.10jqka.com.cn/'+symbol+'/'
#     url_rank = 'http://basic.10jqka.com.cn/mapp/'+symbol+'/a_stock_foucs.json'
#     rsp = rq.get(url=url_rank,headers=h)
#     #市场排名
#     stock_info['all_rank'] = rsp.json()['data']['all_rank']
#     #行业排名
#     stock_info['industry_rank'] = rsp.json()['data']['industry_rank']
#     async with aiohttp.ClientSession() as session:
#         rsp = await session.get(url_info,headers=h)
#         rsp.encoding = 'gb2312'
#         content = await rsp.text()

#         soup = BeautifulSoup(content, 'html.parser')
#         #公司亮点
#         stock_info['lightspot'] = soup.find_all('span',text='公司亮点：')[0].find_next_sibling().string.strip()
#         #主营业务
#         stock_info['major'] = soup.find_all('span',text='主营业务：')[0].find_next_sibling().a['title']
#         #所属申万行业
#         stock_info['industry'] = soup.find_all('span',text='所属申万行业：')[0].find_next_sibling().text
#         #前3贴合概念
#         concepts = []
#         for related_concept in soup.find(class_='newconcept').find_all('a')[:3]:
#             concepts.append(related_concept.text)
#         stock_info['fit_concepts'] = ' '.join(concepts)

#     # return stock_info

# async def scrapStockInfoLoop(symbol,stock_info):
#     await asyncio.gather(*[scrapStockInfo(symbol,stock_info)])

#爬取同花顺股票详情页
def scrapStockInfo(symbol):
    stock_info = {}
    h = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}
    url_info = 'http://basic.10jqka.com.cn/'+symbol+'/'
    url_rank = 'http://basic.10jqka.com.cn/mapp/'+symbol+'/a_stock_foucs.json'
    rsp = rq.get(url=url_rank,headers=h)
    #市场排名
    stock_info['all_rank'] = rsp.json()['data']['all_rank']
    #行业排名
    stock_info['industry_rank'] = rsp.json()['data']['industry_rank']
    rsp = rq.get(url=url_info,headers=h)
    rsp.encoding = 'gb2312'
    soup = BeautifulSoup(rsp.text, 'html.parser')

    #公司亮点
    stock_info['lightspot'] = soup.find_all('span',text='公司亮点：')[0].find_next_sibling().string.strip()
    #主营业务
    stock_info['major'] = soup.find_all('span',text='主营业务：')[0].find_next_sibling().a['title']
    #所属申万行业
    stock_info['industry'] = soup.find_all('span',text='所属申万行业：')[0].find_next_sibling().text
    #前3贴合概念
    concepts = []
    for related_concept in soup.find(class_='newconcept').find_all('a')[:3]:
        concepts.append(related_concept.text)
    stock_info['fit_concepts'] = ' '.join(concepts)

    return stock_info

#获取股票详情
def getStockInfo(request,symbol):
    return HttpResponse(json.dumps(scrapStockInfo(symbol),ensure_ascii=False))

    # stock_info = {}
    # new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(scrapStockInfoLoop(symbol,stock_info))
    # loop.close()

    # return HttpResponse(json.dumps(stock_info,ensure_ascii=False))

#获取股票所属申万行业-----异步爬取
async def getStockIndustry(df,symbol):
    h = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}
    url_info = 'http://basic.10jqka.com.cn/'+symbol+'/'

    async with aiohttp.ClientSession() as session:
        resp = await session.get(url_info,headers=h,ssl=False)
        # print(resp.status)
        resp.encoding = 'gb2312'
        content = await resp.text()
        soup = BeautifulSoup(content, 'html.parser')
        #所属申万行业
        # df.loc[df['代码'] == symbol, ['head_c', 'link_c', 'span_c']] = [[headers_count, links_count, spans_count]]
        df.loc[df['代码'] == symbol, '所属行业'] = [[soup.find_all('span',text='所属申万行业：')[0].find_next_sibling().text]]

async def addIndustryLoop(df):
    await asyncio.gather(*[getStockIndustry(df,symbol) for symbol in df['代码']])

#个股人气榜-实时变动
#单次返回指定 symbol 的股票近期历史数据
def getStockDetailRank(request,symbol):
    #http://guba.eastmoney.com/rank/stock?code=000665
    stock_hot_rank_detail_realtime_em_df = ak.stock_hot_rank_detail_realtime_em(symbol='SZ'+symbol)
    if stock_hot_rank_detail_realtime_em_df.iloc[0,1] == None:
        stock_hot_rank_detail_realtime_em_df = ak.stock_hot_rank_detail_realtime_em(symbol='SH'+symbol)

#获取当前时刻所有概念板块数据
def getBoardConceptData(request):
    stock_df = ak.stock_board_concept_name_em()
    stock_df.drop(index=stock_df[stock_df.板块名称.str.contains('昨日')].index.tolist(),inplace=True)
    stock_df.drop(columns=['最新价','涨跌额','总市值','换手率'],axis=1,inplace=True)
    data_df = stock_df.rename(columns={'领涨股票-涨跌幅':'股票涨跌幅'})
    return HttpResponse(json.dumps(data_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#获取上证指数的实时行情数据
def getShangIndex(request):
    stock_zh_index_spot_df = ak.stock_zh_index_spot()
    data_df = stock_zh_index_spot_df[stock_zh_index_spot_df.名称=='上证指数']
    return HttpResponse(json.dumps(data_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#24h内微博舆情报告中近期受关注的股票
def getWeiboReport(request):
    stock_js_weibo_report_df = ak.stock_js_weibo_report(time_period="CNHOUR12")
    return HttpResponse(json.dumps(stock_js_weibo_report_df.to_dict('records'),cls=DjangoJSONEncoder,ensure_ascii=False))

#资金单位换算
def unitConv(num):
    n = num/10000

    if n < 10000:
        return str(int(n))+'万'
    else:
        return str(round(n/1000,1))+'亿'

#获取最新涨停股票行业分析详情
'''
输出：
名称	类型	描述
序号	int64	-
代码	object	-
名称	object	-
涨跌幅	float64	注意单位: %
最新价	float64	-
成交额	int64	-
流通市值	float64	-
总市值	float64	-
换手率	float64	注意单位: %
封板资金	int64	-
首次封板时间	object	注意格式: 09:25:00
最后封板时间	object	注意格式: 09:25:00
炸板次数	int64	-
涨停统计	object	-
连板数	int64	注意格式: 1 为首板
所属行业	object	-
'''
def getLimitupIndustry(request):
    tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
    #最新交易日
    cur_time = tm.strftime('%H:%M',tm.localtime(tm.time()))
    if tm.strptime(cur_time,'%H:%M') < tm.strptime('09:25','%H:%M') and is_trade_day(datetime.today()): #9点25之前还是显示前一天的情况，且必须是交易日
        today = tool_trade_date_hist_sina_df[tool_trade_date_hist_sina_df.trade_date <= datetime.today().date()].iloc[-2,0]
    else:
        today = tool_trade_date_hist_sina_df[tool_trade_date_hist_sina_df.trade_date <= datetime.today().date()].iloc[-1,0]
    stock_zt_pool_em_df = ak.stock_zt_pool_em(date=today.strftime('%Y%m%d'))
    if stock_zt_pool_em_df.empty:
        return HttpResponse(json.dumps('',cls=DjangoJSONEncoder,ensure_ascii=False))
    # stock_zt_pool_em_df['所属行业'] = stock_zt_pool_em_df['代码'].apply(lambda x:getStockIndustry(x)) //同步返回数据时间太长

    #异步爬虫优化爬取行业信息
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(addIndustryLoop(stock_zt_pool_em_df))
    loop.close()

    stock_zt_pool_em_df['流通市值'] = stock_zt_pool_em_df['流通市值'].apply(lambda x:str(int(x/100000000))+'亿')
    stock_zt_pool_em_df['封板资金'] = stock_zt_pool_em_df['封板资金'].apply(lambda x:unitConv(x))
    stock_zt_pool_em_df['首次封板时间'] = stock_zt_pool_em_df['首次封板时间'].apply(lambda x:''.join([x[:2],':',x[2:4]]))
    industry_statistic = stock_zt_pool_em_df.groupby('所属行业').apply(lambda x:x.to_dict('records')) #返回series类型
    # print(industry_statistic)
    # industry_statistic.sort_values(key=lambda x:len(x),inplace=True)
    return HttpResponse(json.dumps(industry_statistic.to_dict(),cls=DjangoJSONEncoder,ensure_ascii=False))

#获取昨日涨停股票数量
def getPreviousLimitUpCount(request):
    tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
    #最新交易日
    cur_time = tm.strftime('%H:%M',tm.localtime(tm.time()))
    if tm.strptime(cur_time,'%H:%M') < tm.strptime('09:25','%H:%M') and is_trade_day(datetime.today()):
        today = tool_trade_date_hist_sina_df[tool_trade_date_hist_sina_df.trade_date <= datetime.today().date()].iloc[-2,0]
    else:
        today = tool_trade_date_hist_sina_df[tool_trade_date_hist_sina_df.trade_date <= datetime.today().date()].iloc[-1,0]
    stock_zt_pool_previous_em_df = ak.stock_zt_pool_previous_em(date=today.strftime('%Y%m%d'))
    return HttpResponse(json.dumps(len(stock_zt_pool_previous_em_df),cls=DjangoJSONEncoder,ensure_ascii=False))
