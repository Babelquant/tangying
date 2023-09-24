from rest_framework import serializers
from data.models import *
      
class HotStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotStock
        fields = "__all__"

class LimitupStockSerializer(serializers.ModelSerializer):
    time_preview = serializers.SerializerMethodField()

    def get_time_preview(self, obj):
        time_preview = obj.time_preview
        if time_preview == 'None':
            return []
        # 将字符串转换为浮点型数组
        time_preview_array = [float(num) for num in time_preview.strip('[]').split(',') if num and num!='None']
        return time_preview_array

    class Meta:
        model = LimitupStock
        fields = "__all__"

class BidPriceSerializer(serializers.ModelSerializer):
    time_increase = serializers.SerializerMethodField()

    def get_time_increase(self, obj):
        time_increase = obj.time_increase
        time_increase_array = [float(num) for num in time_increase.strip('[]').split(',') if num!='nan' and num]
        return time_increase_array
    
    class Meta:
        model = BidPrice
        fields = "__all__"

class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = "__all__"

class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = "__all__"
        
class StockRealtimeRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRealtimeRank   
        fields = "__all__"

class StockZYSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockZY   
        fields = "__all__"
