from django.urls import path
from data.views import *

# router = routers.DefaultRouter()
# router.register(r'costpredict',CostPredictViewSet)

# urlpatterns = [
#     re_path(r'^', include(router.urls)),
# ]

urlpatterns = [
    #获取热度榜数据
    path(r'hot_stocks', HotStockViewSet.as_view(),name='hotStocks'),
    #获取历史热热度排名
    path(r'historyRank', StockHisRankViewSet.as_view(),name='history_rank'),
    #获取当日涨停股票
    path(r'limitup/list', LimitupStockViewSet.as_view(),name='limitup'),
    #概念策略数据
    path(r'conceptStock/list', ConceptStockDataViewSet.as_view(),name='concept_stock'),
    #集合竞价异动
    path(r'abnormal_bidprice/list', BidPriceAbnormalViewSet.as_view(),name='bidprice'),
    #连板情况
    path(r'continueBoard/list', LimitupStockViewSet.as_view(),name='continue_stock'),
    #获取1进2数据
    path(r'limitup_two/list', LimitupContinueViewSet.as_view(),name='limitup_two'),
    #获取股票主营业务
    path(r'zy', StockZyViewSet.as_view(),name='zy'),
    #热度排名异动
    path(r'rank_big_change', AbnormalStockRankViewSet.as_view(),name='rank_big_change'),
    #获取行业分析数据
    path('industry_statistic/', industryStatistic),
    #获取所有股票信息
    path('all_securities/', getAllSecurities),
    #获取热度概念
    path(r'concept_hot', ConceptHotViewSet.as_view(),name='concept_hot'),
    #获取所有概念信息
    path(r'concept/list', ConceptData.as_view(),name='concept'),
    #获取单只股票蜡烛图数据
    path(r'candlestick', StockCandlestick.as_view(),name='candlestick'),
    #获取个股最新行情
    path('latest_price/<code>/', getLatestPrice),
    #获取个股资料
    path('stock_info/<symbol>/', getStockInfo),
    #获取板块概念数据
    path('board_concept_data/', getBoardConceptData),
    #获取最新涨停股票行业分析详情
    path('limitup_industry/', getLimitupIndustry),
    #概念策略数据
    # path('concept_stock/<str:codes>/', conceptStockData),
    #快速下跌策略数据
    path('sharpfall_strategy/', getSharpfallStrategy),
    #首板策略数据
    path('first_board_strategy/', firstBoardStrategy),
    #获取实时资讯
    path('news/', getNews),
    #获取昨日涨停股票数量
    path('pre_limitup_count/', getPreviousLimitUpCount),
    #获取上证指数实时行情
    path('sz_index/', getShangIndex),
    #24h内微博舆情报告中近期受关注的股票
    path('weibo_report/', getWeiboReport),

]