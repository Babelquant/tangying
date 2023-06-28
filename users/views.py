from django.shortcuts import render

# Create your views here.
from django.contrib import auth
from django.contrib.auth import get_user_model
# from corsheaders.decorators import cors_headers

from rest_framework.views import APIView
from rest_framework.permissions import *
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view,authentication_classes,permission_classes

from rest_framework.permissions import IsAuthenticated,AllowAny

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from users.serializers import *

@api_view(['POST'])
@permission_classes((AllowAny,))
def logIn(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')

    user = auth.authenticate(username=username, password=password)
    if user == None:
        return Response({
            'code': 201,
            'message': '用户名或密码错误'
        })
    token,_ = Token.objects.get_or_create(user=user)
    response = Response({
        'code': 200,
        'data': {
            'token': token.key
        }
    })
    return response

@api_view(['POST'])
@permission_classes((AllowAny,))
def logOut(request):
    # user = auth.authenticate(username=username, password=password)
    # if user == None:
    #     return Response({
    #         'code': 201,
    #         'data': {}
    #     })
    # token,_ = Token.objects.get_or_create(user=user)
    return Response({
        'code': 200,
        'message': 'Successful'
    })

class SignUpViewSet(APIView):  
    permission_classes = [AllowAny]
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('username', openapi.IN_QUERY, description="用户名", type=openapi.TYPE_STRING),
        openapi.Parameter('password', openapi.IN_QUERY, description="密码", type=openapi.TYPE_STRING),
    ])
    def post(self,request):
        query_params = request.query_params.copy()
        query_params['roles'] = "admin"
        # serializer = UserRegisterSerializer(data=request.data)
        serializer = UserRegisterSerializer(data=query_params)
        if serializer.is_valid():
            user = serializer.save()
            # response_data = {
            #     'user_id': user.id,
            #     'username': user.username,
            #     'roles': user.roles,
            # }
            return Response({
                'code': 200,
                "message": "注册成功"
            })
        else:
            return Response({
                "data": None,
                "code": 400,
                "message": serializer.errors
            })

@api_view(['GET'])
@permission_classes((AllowAny,))
def getUserInfo(request):
    #获取请求参数token的值
    token=request.GET.get('token')
    #通过token对象获取关联user对象
    user_info = Token.objects.get(key=token).user
    serializer = UserInfoSerializer(user_info)
    return Response({
        "data": serializer.data,
        "code": 200,
        "message": "请求成功"
    })