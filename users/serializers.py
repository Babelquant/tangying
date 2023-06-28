from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    def get_roles(self, obj):
        return obj.roles.split(',')

    class Meta:
        model = User
        fields = "__all__"

class UserRegisterSerializer(serializers.ModelSerializer):
    # 利用drf中的validators验证username是否唯一
    username = serializers.CharField(required=True, allow_blank=False, validators=[UniqueValidator(queryset=User.objects.all(),message='用户已经存在')])
    password = serializers.CharField(
         style={"input_type": "password"},label="密码", write_only=True,
     )
    def create(self, validated_data):
         user = super(UserRegisterSerializer, self).create(validated_data= validated_data)
         user.set_password(validated_data["password"])
         user.save()
         return user
    class Meta:
         model = User
         fields = ( "username", "password", "roles")