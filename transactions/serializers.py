from rest_framework import serializers
from .models import Transaction, Account, Category

#把資料轉為json

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'account_type', 'balance']

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)  # 新增

    class Meta:
        model = Transaction
        fields = ['id', 'date', 'amount', 'note', 'category', 'category_name', 'category_type', 'account']  # 加入 category_type