from django.shortcuts import render
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder

# Create your views here.

import json
import easytrader as et
from easytrader import remoteclient

try:
    user = remoteclient.use('universal_client',host='192.168.1.3',port='1430')
    user.prepare(user='阿狗M',password='*********')
except:
    pass

#获取资金状况
def balanceInfo(request):
    return HttpResponse(json.dumps(user.balance,cls=DjangoJSONEncoder,ensure_ascii=False))

def buy(request):
    code = request.get['code']
    price = request.get['price']
    amount = request.get['amount']
    print(price)
    return HttpResponse(json.dumps([],cls=DjangoJSONEncoder,ensure_ascii=False))