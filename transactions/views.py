
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import TransactionSerializer, AccountSerializer, CategorySerializer
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction
from .forms import TransactionForm
from django.contrib.auth.decorators import login_required # 未登入不能進入頁面
from .rag import ask_financial_question
from django.http import JsonResponse
from .rag import suggest_category
from .rag import generate_monthly_report
from datetime import datetime

@login_required # 裝飾器 執行這個 function 之前，先確認有沒有登入，沒登入就自動跳轉到登入頁面」
def transaction_list(request):
    transactions = Transaction.objects.filter(account__user=request.user)  # 只撈出目前登入使用者的交易記錄  
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})
    # 把撈出來的資料傳給 transaction_list.html 顯示

@login_required
def transaction_create(request):
    if request.method == 'POST':
        # 如果是「送出資料」這次的請求
        form = TransactionForm(request.POST, user=request.user)    # 把使用者填的資料放進表單
        if form.is_valid():                      # 檢查資料合不合法（金額是不是數字等）
            form.save()                          # 存進資料庫（新增一筆）
            return redirect('transaction_list')  # 存完跳轉回列表頁
    else:
        # 如果是「單純打開頁面」這次的請求
        form = TransactionForm(user=request.user)                 # 給一個空白表單讓使用者填
    return render(request, 'transactions/transaction_form.html', {'form': form})
    # 把表單傳給 transaction_form.html 顯示（GET 時顯示空白表單，POST 驗證失敗時顯示錯誤）

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)  # 去資料庫找這筆資料，找不到就回傳 404
    if request.method == 'POST':
        # 使用者在確認頁面按下「確認刪除」
        transaction.delete()                     # 真正執行刪除
        return redirect('transaction_list')      # 刪完跳轉回列表頁
    return render(request, 'transactions/transaction_confirm_delete.html', {'transaction': transaction})
    # GET 時顯示確認刪除頁面，讓使用者再確認一次，避免誤刪

@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)  # 去資料庫找要修改的那筆，找不到就回傳 404
    if request.method == 'POST':
        # 使用者改完資料按下送出
        form = TransactionForm(request.POST, instance=transaction)  # 把新資料 + 原本那筆綁在一起
        if form.is_valid():                      # 檢查新資料合不合法
            form.save()                          # 更新資料庫（因為有 instance，所以是更新不是新增）
            return redirect('transaction_list')  # 更新完跳轉回列表頁
    else:
        # 使用者第一次打開修改頁面
        form = TransactionForm(instance=transaction)  # 把原本的資料預填進表單，不是空白的
    return render(request, 'transactions/transaction_form.html', {'form': form})
    # 把表單傳給 transaction_form.html 顯示（GET 時預填資料，POST 驗證失敗時顯示錯誤）

@login_required
def dashboard(request):
    # 顯示儀表板頁面，資料由前端 JavaScript 透過 API 撈取後用 Chart.js 畫圖
    return render(request, 'transactions/dashboard.html')




# ModelViewSet 繼承來自 DRF，自動擁有列表、新增、查單筆、修改、刪除五個 API 功能
class TransactionViewSet(viewsets.ModelViewSet):
    # 告訴 DRF 用 TransactionSerializer 把資料轉成 JSON 格式
    serializer_class = TransactionSerializer
    # 只有登入的使用者才能呼叫這個 API，沒登入回傳 403 錯誤
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 覆蓋父類別的 get_queryset，只撈目前登入使用者的交易記錄
        # self.request.user 跟之前的 request.user 一樣，在 class 裡要加 self
        return Transaction.objects.filter(account__user=self.request.user)


class AccountViewSet(viewsets.ModelViewSet):
    # 告訴 DRF 用 AccountSerializer 把資料轉成 JSON 格式
    serializer_class = AccountSerializer
    # 只有登入的使用者才能呼叫這個 API
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只撈目前登入使用者自己的帳戶
        return Account.objects.filter(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    # 告訴 DRF 用 CategorySerializer 把資料轉成 JSON 格式
    serializer_class = CategorySerializer
    # 只有登入的使用者才能呼叫這個 API
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 分類是全部使用者共用的，所以撈全部，不用篩選使用者
        return Category.objects.all()
    


@login_required
def financial_chat(request):
    answer = None

    if request.method == 'POST':
        question = request.POST.get('question')
        if question:
            answer = ask_financial_question(request.user, question)

    return render(request, 'transactions/financial_chat.html', {
        'answer': answer
    })


@login_required
def suggest_category_view(request):
    # 接收前端傳來的備註文字（例如「麥當勞」）
    note = request.GET.get('note', '')
    if note:
        # 呼叫 rag.py 的 suggest_category，讓 Groq 根據備註推薦分類
        category = suggest_category(note, request.user)
        # 回傳 JSON 格式，不是 HTML 頁面，給 JavaScript 讀取用
        return JsonResponse({'category': category})
    return JsonResponse({'category': ''})


@login_required
def monthly_report(request):
    # 取得目前的年月，例如 "2026-07"
    current_month = datetime.now().strftime('%Y-%m')

    # 呼叫 rag.py 產生財務報告
    report = generate_monthly_report(request.user, current_month)

    return render(request, 'transactions/monthly_report.html', {
        'report': report,
        'month': current_month,
    })