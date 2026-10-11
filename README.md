# 💰 Finance Tracker

一個以 Django 打造的個人財務追蹤平台，支援 Google 登入、收支記錄管理、資料視覺化，並整合 RAG（Retrieval-Augmented Generation）讓使用者能用自然語言查詢自己的財務狀況。

> 🚧 **開發中**：目前已完成核心功能，頁面美化與雲端部署進行中。

---

## ✨ 功能特色

### 核心功能
- **完整 CRUD**：新增、查看、修改、刪除交易記錄
- **Google OAuth 登入**：使用 `django-allauth` 串接 Google 帳號
- **資料隔離**：每位使用者只能看到與操作自己的帳戶與交易
- **日期選擇器**：表單使用 HTML5 日期選擇，輸入更方便

### REST API
- 使用 Django REST Framework 提供 `transactions`、`accounts`、`categories` 三組 API
- 使用 `DefaultRouter` 自動產生路由（列表、新增、查單筆、修改、刪除）
- 需登入才能存取，且只回傳目前使用者自己的資料

### 資料視覺化
- **支出分類圓餅圖**：各分類支出比例
- **每月收支趨勢圖**：多個月份顯示折線圖，單一月份自動切換為長條圖
- **月份篩選**：下拉選單切換要查看的月份
- 前端以 JavaScript `fetch` 呼叫 REST API，再用 Chart.js 繪圖

### AI 功能（RAG）
| 功能 | 說明 |
|---|---|
| 💬 智慧財務問答 | 用自然語言提問（例如「我 7 月餐飲花多少？」），系統先用 Pinecone 找出最相關的交易，再交給 LLM 回答 |
| 🏷️ 自動分類建議 | 輸入備註後，AI 從現有分類中推薦最適合的一個 |
| 📊 每月財務報告 | 根據當月交易記錄，自動生成收支分析與理財建議 |

---

## 🛠️ 技術棧

| 類別 | 技術 |
|---|---|
| 後端 | Python 3.12、Django 6 |
| API | Django REST Framework |
| 資料庫 | MySQL（PyMySQL） |
| 登入 | django-allauth（Google OAuth） |
| 前端 | Django Template、Bootstrap 5、Chart.js |
| LLM | Groq API（`llama-3.1-8b-instant`） |
| 向量資料庫 | Pinecone（Integrated Embedding：`llama-text-embed-v2`） |
| AI 框架 | LangChain（`langchain-groq`） |

---

## 🧱 系統架構

```
使用者瀏覽器
     │
     ├── 一般頁面 ──► urls.py ──► views.py ──► templates (HTML)
     │
     ├── 圖表資料 ──► REST API (DRF ViewSet + Serializer) ──► JSON ──► Chart.js
     │
     └── AI 功能 ──► views.py ──► rag.py ──┬─► Pinecone（搜尋相關交易）
                                           └─► Groq（生成回答）
                                
資料庫：MySQL（Account / Category / Transaction）
```

### 資料表關聯

```
User ──< Account ──< Transaction >── Category
```

- 一位使用者可擁有多個帳戶（現金、信用卡、銀行帳戶）
- 一個帳戶有多筆交易
- 每筆交易屬於一個分類（收入 / 支出）

---

## 📁 專案結構

```
finance-tracker/
├── config/                  # 專案設定（settings.py、總路由 urls.py）
├── accounts/                # 使用者相關 app
├── transactions/            # 交易功能 app
│   ├── models.py            # Account、Category、Transaction
│   ├── forms.py             # TransactionForm
│   ├── views.py             # 網頁 view + API ViewSet
│   ├── serializers.py       # DRF Serializer
│   ├── rag.py               # Pinecone + Groq（問答、分類建議、月報告）
│   ├── urls.py              # 網頁路由 + API 路由
│   └── templates/transactions/
├── manage.py
├── requirements.txt
└── .env                     # 環境變數（不要上傳）
```

---

## 🚀 本機安裝與執行

### 1. 下載專案並建立虛擬環境

```bash
git clone <你的 repo 網址>
cd finance-tracker

python3.12 -m venv ftenv
source ftenv/bin/activate        # Windows: ftenv\Scripts\activate
pip install -r requirements.txt
```

> ⚠️ 建議使用 **Python 3.12**。部分 AI 相關套件（如 `langchain-pinecone`）尚未支援 Python 3.14。

### 2. 建立 MySQL 資料庫

```sql
CREATE DATABASE finance_db CHARACTER SET utf8mb4;
```

### 3. 設定環境變數

在專案根目錄建立 `.env`：

```bash
# 資料庫
DB_NAME=finance_db
DB_USER=root
DB_PASSWORD=你的MySQL密碼
DB_HOST=localhost
DB_PORT=3306

# Google OAuth
GOOGLE_CLIENT_ID=你的用戶端ID
GOOGLE_CLIENT_SECRET=你的用戶端密鑰

# AI 服務
GROQ_API_KEY=你的Groq金鑰
PINECONE_API_KEY=你的Pinecone金鑰
PINECONE_INDEX=finance-tracker
```

### 4. 初始化資料庫並啟動

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 5. 設定 Google 登入（Admin 後台）

1. 前往 `http://127.0.0.1:8000/admin`
2. **Sites**：把 `example.com` 改成 `127.0.0.1:8000`
3. **Social Applications** → Add：Provider 選 Google，填入 Client ID 與 Secret，並選取 Site
4. Google Cloud Console 的「已授權的重新導向 URI」加入：
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```

### 6. 建立 Pinecone Index

在 Pinecone 建立名為 `finance-tracker` 的 index，並選擇 Integrated Embedding（`llama-text-embed-v2`）。

---

## 🔗 主要路由

| 路徑 | 說明 |
|---|---|
| `/transactions/` | 交易記錄列表 |
| `/transactions/create/` | 新增交易（含 AI 分類建議） |
| `/transactions/<id>/update/` | 修改交易 |
| `/transactions/<id>/delete/` | 刪除交易 |
| `/dashboard/` | 財務儀表板（圓餅圖、趨勢圖） |
| `/chat/` | 智慧財務問答 |
| `/monthly-report/` | 每月財務分析報告 |
| `/api/` | REST API 入口 |
| `/api/transactions/` | 交易 API |
| `/api/accounts/` | 帳戶 API |
| `/api/categories/` | 分類 API |
| `/admin/` | Django 後台 |

---

## 🗺️ 開發進度

- [x] 環境建置、MySQL 串接
- [x] 資料庫設計（Account / Category / Transaction）
- [x] 完整 CRUD
- [x] Google OAuth 登入、使用者資料隔離
- [x] REST API（Django REST Framework）
- [x] 資料視覺化（Chart.js）
- [x] RAG 智慧財務問答（Pinecone + Groq）
- [x] AI 自動分類建議
- [x] AI 每月財務報告
- [ ] 頁面美化（導覽列、登入頁、首頁）
- [ ] 部署到 Railway
- [ ] Docker 容器化
- [ ] 金流串接（Stripe 測試模式）

---

## 📝 開發筆記

- **為什麼用 RAG？** 直接把所有交易傳給 LLM 會隨資料量增加而變慢、變貴。透過 Pinecone 先做語意搜尋，只把最相關的幾筆交給 LLM，回應更快也更省 token。
- **為什麼改用 Python 3.12？** 初期使用 Python 3.14 時，`langchain-pinecone` 的相依套件無法安裝，因此改用 3.12 重建虛擬環境。

---

## 📄 License

個人學習與作品集專案。
