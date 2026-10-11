from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DefaultRouter 自動幫每個註冊的 ViewSet 產生五條路由（列表、新增、查單筆、修改、刪除）
router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction-api')
router.register(r'accounts', views.AccountViewSet, basename='account-api')
router.register(r'categories', views.CategoryViewSet, basename='category-api')

urlpatterns = [
    # 原本的網頁路由
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('dashboard/', views.dashboard, name='dashboard'), #JavaScript 透過 API 撈取後用 Chart.js 畫圖的路由
    path('chat/', views.financial_chat, name='financial_chat'),
    # 提供一個 API endpoint，讓前端可以用 AJAX 呼叫，取得自動分類建議
    path('suggest-category/', views.suggest_category_view, name='suggest_category'),
    path('monthly-report/', views.monthly_report, name='monthly_report'),



    # API 路由
    path('api/', include(router.urls)),
    
]