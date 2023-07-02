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
    #获取最新排名前十的股票
    path('hot10_stocks/', getHotTop10Stocks),
    #获取当日涨停股票
    path(r'limitup/list', LimitupStockViewSet.as_view(),name='limitup'),
    #概念策略数据
    path(r'conceptStock/list', ConceptStockData.as_view(),name='concept_stock'),
    #上板情况
    path('limitup_statistic/', limitupStatistic),
    #获取概念分析数据
    path('concept_statistic/', conceptStatistic),
    #获取行业分析数据
    path('industry_statistic/', industryStatistic),
    #获取所有股票信息
    path('all_securities/', getAllSecurities),
    #获取所有概念信息
    path(r'concept/list', ConceptData.as_view(),name='concept'),
    #获取单只股票蜡烛图数据
    path('candlestick/<code>/', getCandlestick),
    #获取个股最新行情
    path('latest_price/<code>/', getLatestPrice),
    #获取个股资料
    path('stock_info/<symbol>/', getStockInfo),
    #获取板块概念数据
    path('board_concept_data/', getBoardConceptData),
    #获取最新涨停股票行业分析详情
    path('limitup_industry/', getLimitupIndustry),
    #布林策略数据
    path('boll_strategy/', bollStrategyData),
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
