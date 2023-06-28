"""
scrape hot stocks
"""

import json,time,os,math
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup
from tangying.common import getSqliteEngine
from data.models import *
from datetime import *
from django.db.models import Count
import akshare as ak

class HotRankStocks:
    def __init__(self):
        self.url = "https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/a/hour/data.txt"
        self.stocks_head = ['Name','Rank','Change','Concept','Popularity','Express','Time']
        # self.date = time.strftime('%m-%d',time.localtime(time.time()))
        self.date = datetime.today().strftime("%m-%d")
        self.header ={
            'Host': 'eq.10jqka.com.cn',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G9810 Build/QP1A.190711.020; wv) \
            AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 \
            Hexin_Gphone/10.13.02 (Royal Flush) hxtheme/0 innerversion/G037.08.462.1.32 userid/-640913281 hxNewFont/1',
            'Referer': 'https://eq.10jqka.com.cn/webpage/ths-hot-list/index.html?showStatusBar=true',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'com.hexin.plat.android'
        }

    #获取热度榜所有股票，返回dataFrame
    def getHotStocksDataFrame(self):
        rsp = rq.get(url=self.url,headers=self.header)
        rsp_body = rsp.json()
        hot_list = parseHotStockPackage(rsp_body)
   
        #返回股票热度榜表单
        return pd.DataFrame(data=hot_list,columns=self.stocks_head) 

    #获取热度榜所有股票，返回list
    def getHotStocksList(self):
        ls = [self.stocks_head]
        rsp = rq.get(url=self.url,headers=self.header)
        rsp_body = rsp.json()
        hot_list = parseHotStockPackage(rsp_body)
        ls.extend(hot_list)
        return ls

class LimitUpStocks:
    def __init__(self):
        self.url = "https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool"
        self.stocks_head = ['Name', 'Code', 'Latest', 'Currency_value', 'Reason_type', 'Limitup_type', 'High_days', 'Change_rate', 'Date']
        # self.date = time.strftime('%m-%d',time.localtime(time.time()))
        self.date = datetime.today().strftime("%m-%d")
        self.header = {
                'Host': 'data.10jqka.com.cn',
                'Connection': 'keep-alive',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; HD1900 Build/QKQ1.190716.003; wv) \
                AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile \
                Safari/537.36 Hexin_Gphone/10.40.10 (Royal Flush) hxtheme/1 innerversion/\
                G037.08.577.1.32 followPhoneSystemTheme/1 userid/475543965 \
                hxNewFont/1 isVip/0 getHXAPPFontSetting/normal getHXAPPAdaptOldSetting/0',
                'Sec-Fetch-Mode': 'cors',
                'X-Requested-With': 'com.hexin.plat.android',
                'Sec-Fetch-Site': 'same-origin',
                'Referer': 'https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                }

    def requestParam(self,page=1):
        return  {'page': page,'limit': 15,'field': '199112,10,9001,330323,330324,330325,9002,330329,\
                133971,133970,1968584,3475914,9003,9004','filter': 'HS,GEM2STAR','order_field': 330324,\
                'order_type': 0,'data': '','_': 1657151054188}

    #获取涨停所有股票
    def getLimitUpStocks(self):
        rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam())
        rsp_body = rsp.json()
        one_page_data = parseLimitUpStockPackage(rsp_body)
        page = rsp_body['data']['page']
        page_count = math.ceil(page['total']/page['limit'])

        #获取翻页全量数据
        full_stocks = []
        for i in range(2,page_count+1):
            rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam(i))
            one_page_data.extend(parseLimitUpStockPackage(rsp.json()))        

        #返回股票详情表单
        return pd.DataFrame(data=one_page_data,columns=self.stocks_head)
        
#解析热度榜数据包
def parseHotStockPackage(body):
    date = datetime.now()
    # date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if body['status_code'] == 0:
        # date = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        rows = []
        infos = body['data']['stock_list']
        for info in infos:
            row = [ info['name'],info['order'],info['hot_rank_chg'],\
                    '&'.join(info['tag']['concept_tag']),float(info['rate'])/10000,info['tag'].get('popularity_tag',None),date]
            rows.append(row)
        return rows

#解析涨停池数据包
def parseLimitUpStockPackage(body):
    if body['status_code'] == 0:
        date = datetime.now()
        rows = []
        infos = body['data']['info']
        # print(infos)
        last_date = LimitupStocks.objects.values('Date').distinct().last()['Date']
        for info in infos:
            if info['high_days'] == '3天2板' or info['high_days'] == '4天2板':
                info['high_days'] = '首板'
            if info['high_days'] == '4天2板':
                info['high_days'] = '2天2板'
            if info['high_days'] == '5天3板':
                #判断前一个交易日是否涨停
                if LimitupStocks.objects.filter(Date__range=(last_date-timedelta(days=1),last_date),Name=info['name']).exists():
                    info['high_days'] = '2天2板'

            row = [ info['name'],info['code'],info['latest'],int(info['currency_value']/100000000),\
                    info['reason_type'],info['limit_up_type'],info['high_days'],\
                    str(int(info['change_rate']))+"%",date ]
            rows.append(row)
        return rows


def hotStocks2Sqlite():
    hot_stocks = HotRankStocks()
    try:
        # conn = sqlConn.connect(
        #     host = "localhost",
        #     port = 3306,
        #     user = "root",
        #     password = "888888",
        #     database = "tangying"
        # )
        # print("connect mysql success.")
        # conn.start_transaction()
        # cursor = conn.cursor(prepared=True)
        # sql = "INSERT into hotstocks VALUES(%s,%s,%s,%s,%s,%s,%s)"
        # cursor.execute(sql,("中通客车", 1, 0, "燃料电池&新能源汽车", 432514325.2, None, "2022-04-23 08:33:45"))
        # conn.commit()

        hot_stocks_df = hot_stocks.getHotStocksDataFrame()
        engine = getSqliteEngine()
        hot_stocks_df.to_sql("hotstocks",engine,index=False,if_exists="append")
    except Exception as e:
        print("err:",e)
        # if "conn" in dir():
        #     conn.rollback()
    finally:
        pass
        # if "engine" in dir():
        #     engine.close()

#涨停池股票入库
#拆分涨停原因
def limitupStocks2Sqlite():
    limitup_stocks = LimitUpStocks()
    try:
        limitup_stocks_df = limitup_stocks.getLimitUpStocks()
        # limitup_stocks_df.loc('Currency_value')/10^8

        #拆分涨停原因
        rows = []
        for _,row in limitup_stocks_df.iterrows():
            for reason in row.loc['Reason_type'].split('+'):
                # row.loc['Reason_type'] = reason
                new_row = row.copy()
                new_row.Reason_type = reason
                new_row.Date = new_row.Date.strftime('%Y-%m-%d')
                rows.append(new_row)
        new_limitup_stocks_df = pd.DataFrame(rows,columns=limitup_stocks.stocks_head).reset_index(drop=True)
   
        if LimitupStocks.objects.last().Date.strftime('%Y%m%d') == datetime.now().strftime('%Y%m%d'):
            LimitupStocks.objects.filter(Date__gte=datetime.now()-timedelta(days=1)).delete()
        engine = getSqliteEngine()
        new_limitup_stocks_df.to_sql("limitupstocks",engine,index=False,if_exists="append")
    except Exception as e:
        print(e)

def allSecurities2Sqlite():
    stock_sh_a_spot_em_df = ak.stock_sh_a_spot_em()[['代码','名称']]
    stock_sz_a_spot_em_df = ak.stock_sz_a_spot_em()[['代码','名称']]
    stock_a_spot_em_df = pd.concat([ak.stock_sh_a_spot_em()[['代码','名称']],ak.stock_sz_a_spot_em()[['代码','名称']]])
    stock_a_spot_em_df.rename(columns={'代码':'code','名称':'value'},inplace=True)
    stock_a_spot_em_df.reset_index(drop=True)

    engine = getSqliteEngine()
    # print(all_stocks)
    stock_a_spot_em_df.to_sql("securities",engine,index_label='id',if_exists="replace")   
    # print(engine.execute("SELECT * FROM securities").fetchall())

def allConcept2Sqlite():
    #获取概念
    stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()[['概念名称','代码']].copy()
    stock_board_concept_name_ths_df.rename(columns={'概念名称':'name','代码':'code'},inplace=True)
    #获取行业
    stock_board_industry_name_ths_df = ak.stock_board_industry_name_ths()
    #合并
    stock_board_name_ths_df = pd.concat([stock_board_concept_name_ths_df,stock_board_industry_name_ths_df])
    stock_board_name_ths_df.drop_duplicates(subset=['code'],inplace=True)
    engine = getSqliteEngine()
    stock_board_name_ths_df.to_sql("concepts",engine,index_label='id',if_exists="replace")

