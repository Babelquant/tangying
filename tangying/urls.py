"""tangying URL Configuration
"""
from django.urls import path,include,re_path
from rest_framework import permissions,routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from data.views import *
from users.views import *

#自动生成crud接口
# from data.views import CostPredictViewSet
# router = routers.DefaultRouter()
# router.register(r'costpredict',CostPredictViewSet)

urlpatterns = [
    path('tangying/user/login', logIn),
    path('tangying/user/logout', logOut),
    path('tangying/user/signUp', SignUpViewSet.as_view(),name='signUp'),
    path('tangying/user/info', getUserInfo),
]

schema_view = get_schema_view(
    openapi.Info(
        title="TangYing API",
        default_version='v1',
        description="Test description",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    re_path(r'^data/', include('data.urls')),
    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
