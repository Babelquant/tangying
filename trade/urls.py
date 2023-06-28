from django.urls import path
from trade.views import *


urlpatterns = [
    #获取资金情况
    path('balance/', balanceInfo),
    #买入
    path('buy/', buy),

]