import os
import requests
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# 初始化 Pinecone 客戶端
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = os.getenv('PINECONE_INDEX')

# 初始化 Groq LLM
llm = ChatGroq(
    api_key=os.getenv('GROQ_API_KEY'),
    model_name='llama-3.1-8b-instant'
)


def sync_transactions_to_pinecone(user):
    """
    把使用者的交易記錄同步到 Pinecone
    - 用 Pinecone Integrated Embedding（llama-text-embed-v2）自動轉成向量
    - 不需要 OpenAI API Key
    """
    from .models import Transaction

    # 從資料庫撈出這個使用者的所有交易記錄
    transactions = Transaction.objects.filter(account__user=user)

    # 建立空 list
    records = []

    for t in transactions:
        # 把交易轉成自然語言文字
        text = f"{t.date} | {t.category} | {t.amount}元 | {t.note}"

        # Pinecone Integrated Embedding 的格式
        # _id：唯一識別碼
        # text：要轉成向量的文字，Pinecone 自動處理
        records.append({
            '_id': f"transaction_{user.id}_{t.id}",
            'text': text,
            'date': str(t.date),
            'amount': str(t.amount),
            'category': str(t.category),
            'note': t.note,
        })

    # 有資料才執行
    if records:
        index = pc.Index(index_name)
        # 用 namespace 隔離不同使用者的資料
        index.upsert_records(namespace="transactions", records=records)


def ask_financial_question(user, question):
    """
    智慧財務問答（RAG 版本）
    - 先用 Pinecone 找出跟問題最相關的交易記錄
    - 只把相關的幾筆傳給 Groq，不用傳全部
    - 速度更快、token 更少
    """
    # 取得 Pinecone index
    index = pc.Index(index_name)

    # 用問題去 Pinecone 搜尋最相關的 5 筆交易記錄
    # Pinecone 會自動把問題轉成向量，再找最相近的資料
    results = index.search(
        namespace="transactions",
        query={
            'inputs': {'text': question},
            'top_k': 5,  # 只取最相關的 5 筆
        },
        fields=['text']
    )

    # 把搜尋結果整理成文字
    relevant_records = results.get('result', {}).get('hits', [])
    if relevant_records:
        context = '\n'.join([r['fields']['text'] for r in relevant_records])
    else:
        context = "找不到相關交易記錄"

    # 把相關交易記錄 + 問題丟給 Groq
    messages = [
        SystemMessage(content=f"""你是一個財務助理，根據以下相關交易記錄回答問題。
請用繁體中文回答，回答要簡潔清楚。

相關交易記錄：
{context}
"""),
        HumanMessage(content=question)
    ]

    response = llm.invoke(messages)
    return response.content


def suggest_category(note, user):
    """根據備註自動建議分類"""
    from .models import Category

    # 撈出所有分類名稱
    categories = Category.objects.values_list('name', flat=True)
    category_list = '、'.join(categories)

    messages = [
        SystemMessage(content=f"""你是一個財務分類助理。
使用者會輸入一段交易備註，請從以下分類中選出最適合的一個，只回答分類名稱，不要有其他文字。

可選分類：{category_list}
"""),
        HumanMessage(content=note)
    ]

    response = llm.invoke(messages)
    return response.content.strip()


def generate_monthly_report(user, year_month):
    """產生每月財務分析報告"""
    from .models import Transaction

    # 撈出這個使用者，指定月份的交易記錄
    transactions = Transaction.objects.filter(
        account__user=user,
        date__startswith=year_month
    )

    # 把交易記錄整理成文字
    transaction_text = '\n'.join([
        f"{t.date} | {t.category} | {t.amount}元 | {t.note}"
        for t in transactions
    ])

    # 組合訊息丟給 Groq，請它生成分析報告
    messages = [
        SystemMessage(content=f"""你是一個財務分析師，請根據以下交易記錄生成一份簡短的月度財務分析報告。
用繁體中文回答，包含：總收入、總支出、最大支出分類、一個理財建議。

交易記錄：
{transaction_text}
"""),
        HumanMessage(content="請生成本月財務報告")
    ]

    response = llm.invoke(messages)
    return response.content