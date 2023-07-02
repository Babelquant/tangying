from rest_framework import serializers
from data.models import *
      
class HotStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotStock
        fields = "__all__"

class LimitupStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = LimitupStock
        fields = "__all__"

class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = "__all__"

class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = "__all__"

class StockRank(serializers.ModelSerializer):
    rank = serializers.JSONField(required=False, default=list)

    class Meta:
        model = 'stockrank'   
        fields = "__all__"

class StockZY(serializers.ModelSerializer):
    class Meta:
        model = 'stockzy'   
        fields = "__all__"