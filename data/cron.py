"""
scrape hot stocks
"""

import sys,time,os,math
import pandas as pd
import requests as rq
import django
from django.http import QueryDict

from bs4 import BeautifulSoup
# 获取项目 settings.py 文件的路径
sys.path.append("/usr/local/tangying")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tangying.settings")
django.setup()
from data.models import *
from datetime import *
from django.db.models import Count
import akshare as ak

from sqlalchemy import create_engine

engine = create_engine('mysql' + '://' + 
                       'root' + ':' +
                       '12345678' + '@' +
                       '127.0.0.1' + '/' + 
                       'tangying')

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

class LimitUpStock:
    def __init__(self):
        self.url = "https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool"
        self.stocks_head = ['name', 'code', 'latest', 'currency_value', 'reason_type', 'limit_up_type', 'high_days', 'change_rate', 
                            'first_limit_up_time', 'last_limit_up_time', 'is_new', 'is_again_limit', 'order_amount', 'date']
        # self.date = datetime.today().strftime("%m-%d")
        self.date = date.today()
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
        rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam()).json()
        if rsp['status_code'] == 0:
            data = rsp['data']['info']
            page = rsp['data']['page']
            page_count = math.ceil(page['total']/page['limit'])

            #获取翻页全量数据
            for i in range(2,page_count+1):
                rsp = rq.get(url=self.url,headers=self.header,params=self.requestParam(i)).json()
                data.extend(rsp['data']['info'])  
            for d in data:
                d['date'] = self.date
        else:
            print("access error.")
            return pd.DataFrame()      

        #返回股票详情表单
        return pd.DataFrame(data=data,columns=self.stocks_head)
        
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
        print(infos)
        last_date = LimitupStock.objects.values('date').distinct().last()['date']
        for info in infos:
            if info['high_days'] == '3天2板' or info['high_days'] == '4天2板':
                info['high_days'] = '首板'
            if info['high_days'] == '4天2板':
                info['high_days'] = '2天2板'
            if info['high_days'] == '5天3板':
                #判断前一个交易日是否涨停
                if LimitupStock.objects.filter(Date__range=(last_date-timedelta(days=1),last_date),Name=info['name']).exists():
                    info['high_days'] = '2天2板'

            row = [ info['name'],info['code'],info['latest'],int(info['currency_value']/100000000),\
                    info['reason_type'],info['limit_up_type'],info['high_days'],\
                    str(int(info['change_rate']))+"%",date ]
            rows.append(row)
        return rows


def hotStocks2Sqlite():
    hot_stocks = HotRankStocks()
    try:
        hot_stocks_df = hot_stocks.getHotStocksDataFrame()
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
    limitup_stocks = LimitUpStock()
    limitup_stocks_df = limitup_stocks.getLimitUpStocks()

    for item in limitup_stocks_df.to_dict(orient='records'):
        LimitupStock.objects.update_or_create(code=item['code'], date=item['date'], defaults=item)

    # #拆分涨停原因
    # rows = []
    # for _,row in limitup_stocks_df.iterrows():
    #     for reason in row.loc['Reason_type'].split('+'):
    #         # row.loc['Reason_type'] = reason
    #         new_row = row.copy()
    #         new_row.Reason_type = reason
    #         new_row.Date = new_row.Date.strftime('%Y-%m-%d')
    #         rows.append(new_row)
    # new_limitup_stocks_df = pd.DataFrame(rows,columns=limitup_stocks.stocks_head).reset_index(drop=True)

    # if LimitupStock.objects.last().Date.strftime('%Y%m%d') == datetime.now().strftime('%Y%m%d'):
    #     LimitupStock.objects.filter(Date__gte=datetime.now()-timedelta(days=1)).delete()
    # new_limitup_stocks_df.to_sql("limitupstocks",engine,index=False,if_exists="append")
    # except Exception as e:
    #     print(e)

def conceptUpdate():
    stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()[['概念名称','代码']]
    stock_board_concept_name_ths_df_re = stock_board_concept_name_ths_df.rename(columns={'概念名称':'name','代码':'code'})
    stock_board_industry_name_ths_df = ak.stock_board_industry_name_ths()
    stock_board_name_ths_df = pd.concat([stock_board_concept_name_ths_df_re,stock_board_industry_name_ths_df])
    stock_board_name_ths_df.drop_duplicates(subset=['code'],inplace=True)
    stock_board_name_ths_df.to_sql("concept",engine,index_label='id',if_exists="replace")

def securityUpdate():
    stock_sh = ak.stock_sh_a_spot_em()[['代码','名称','最新价','流通市值','60日涨跌幅','年初至今涨跌幅']]
    stock_sh['srcSecurityCode'] = "SH" + stock_sh['代码']
    stock_sz = ak.stock_sz_a_spot_em()[['代码','名称','最新价','流通市值','60日涨跌幅','年初至今涨跌幅']]
    stock_sz['srcSecurityCode'] = "SZ" + stock_sz['代码']
    stock_a_spot_em_df = pd.concat([stock_sh,stock_sz])
    stock_a_spot_em_df.rename(columns={'代码':'code','名称':'value','最新价':'latest','流通市值':'currency_value','60日涨跌幅':'sixty_days_increase','年初至今涨跌幅':'year_increase'},inplace=True)
    stock_a_spot_em_df.reset_index(drop=True)   
    print(stock_a_spot_em_df.to_markdown())
    stock_a_spot_em_df.to_sql("security",engine,index_label='id',if_exists="replace") 

def stockZyUpdate():
    code_list = Security.objects.values_list('code', flat=True)
    for code in code_list:
        if code.startswith("300"):
            continue
        print(code)
        stock_zyjs_ths_df = ak.stock_zyjs_ths(symbol="000066")
        data = {
            'code': code,
            'zyyw': stock_zyjs_ths_df.loc[0,'主营业务'],
            'jyfw': stock_zyjs_ths_df.loc[0,'经营范围']
        }
        StockZY.objects.update_or_create(code=code,defaults=data)


# limitupStocks2Sqlite()
# securityUpdate()
# conceptUpdate()
# stockZyUpdate()