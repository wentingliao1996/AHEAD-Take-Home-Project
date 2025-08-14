# AHEAD-Take-Home-Project

## 專案需求

### US-MVP-001: 簡單檔案上傳
**作為** 任何使用者  
**我想要** 能夠上傳單一檔案  
**這樣我就能** 快速分享檔案給其他人  

**接受條件**：
- 支援單一檔案上傳 (最大 1000MB)，需驗證檔案大小和格式驗證
- 只支援格式：`FCS`
- 上傳後立即產生可公開的短連結與存取檔案資訊（檔名、檔案大小、上傳時間、FCS 版本）
- 需要 logging 總上傳時間（效能是評估重點）

---

### US-MVP-002: 私人檔案上傳
**作為** 登入使用者  
**我想要** 能夠上傳私人檔案  
**這樣我就能** 控制誰可以存取我的檔案  

**接受條件**：
- 基本的 Email + 密碼註冊（資安是評估重點）
- 登入使用者可以選擇檔案為「私人」
- 私人檔案需要登入才能存取
- 只有檔案擁有者可以存取私人檔案
- 需要 logging 使用者行為，包含使用者名稱、登入、登出、將檔案設定為公開等活動

---

### US-MVP-003: 簡單背景任務
**作為** 系統程式  
**我想要** 取得使用者的使用狀況  
**這樣我就能** 提供基本的儲存統計  

**接受條件**：
- 呼叫統計 API 後觸發的背景計算
- 為了不讓使用者等待，需先回傳任務 ID 與處理狀態  
  狀態有：`pending`、`running`、`finished`
- 需要在背景計算中 logging 以上每一種狀態
- 使用者可以根據任務 ID 查看儲存使用量
- **對列出每一個檔案**：
  - 列出的檔名、檔案大小、上傳時間、FCS 版本、FCS 檔中所有的 `PnN`（Short name for parameter n）、與 event 數
  - 參考：[FlowIO Tutorial — FlowIO documentation](https://flowio.readthedocs.io/)
- **對單一使用者**：
  - 列出上傳的檔案總數以及硬碟總使用量

## 說明

此專案提供一個以 FastAPI 為核心的檔案上傳與任務背景處理服務，支援使用者註冊/登入（JWT）、FCS 檔案上傳與管理、Celery 背景計算、以及以 Alembic 進行資料庫版本管理。

### 主要技術架構
- **後端框架**: FastAPI + Starlette
- **資料庫**: PostgreSQL（SQLAlchemy）
- **背景任務**: Celery（Broker/Backend: Redis）
- **驗證**: JWT（`python-jose`），HTTP Bearer
- **檔案處理**: 分段串流寫入、FCS 解析（`flowio`）
- **容器**: Docker、docker-compose

### 專案亮點
- **可上傳大型 FCS 檔案**：串流寫入避免記憶體爆量，允許設定單檔大小上限。
- **公開/私人檔案**：支援匿名公開上傳或綁定使用者私人檔案，並可切換可見性。
- **完整活動紀錄**：登入、登出、上傳、讀取、可見性變更皆記錄於 `activity_logs`。
- **背景任務與狀態查詢**：以 Celery 建立統計任務，支援進度/結果輪詢。
- **自訂 OpenAPI 與 Bearer 安全機制**：Swagger UI 內可直接帶入 Bearer Token 測試。


## 環境建置指南

### 1) 準備 .env
在專案根目錄建立 `.env` 檔：
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=thp

# JWT
SECRET_KEY=please_change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis（docker-compose 服務名）
REDIS_HOST=redis
REDIS_PORT=6379

# 檔案上傳
UPLOAD_DIR=uploads
MAX_FILE_MB=1000
```

### 2) 使用 Make 指令（建議）
- 啟動服務（API、DB、Redis）：
```bash
make start
```

相關服務：
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Flower: `http://localhost:5555`


## API 文件

Swagger 互動式文件：[`http://localhost:8000/docs`](http://localhost:8000/docs)

以下為主要路由（所有路由預設於 OpenAPI 設置了 Bearer 安全機制；未標註「需登入」者採可選驗證）：

### Authentication `/auth`
- POST `/auth/register`
  - 傳入：`{ "email": EmailStr, "password": str }`
  - 回傳：`{ "access_token": str, "token_type": "bearer" }`
- POST `/auth/login`
  - 傳入：`{ "email": EmailStr, "password": str }`
  - 回傳：`{ "access_token": str, "token_type": "bearer" }`
- POST `/auth/logout`（需登入）
  - 回傳：`{ "message": "Logged out successfully" }`

範例（登入）：
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'
```

### Files `/files`
- POST `/files/upload`（可選登入）
  - multipart form：
    - `file`: .fcs 檔案
    - `is_public`: bool（預設 true）
  - 回傳：
    ```json
    {
      "short_link": "/files/{slug}",
      "filename": "*.fcs",
      "size": number,
      "fcs_version": "FCSx.y",
      "is_public": true,
      "owner_id": 1
    }
    ```
- GET `/files`（可選登入）
  - 未登入：回傳公開檔案列表
  - 已登入：回傳公開 + 該用戶私人檔案列表
- PUT `/{slug}/visibility`（需登入且為檔案擁有者）
  - 參數：`slug`、`is_public`（query 或 body）
  - 回傳：`{ "message": "File visibility updated successfully" }`

上傳範例：
```bash
curl -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/file.fcs" \
  -F "is_public=true"
```

### Statistics `/stats`
- POST `/stats/tasks`（需登入）
  - 建立背景任務，回傳：`{ "task_id": str, "status": "PENDING" }`
- GET `/stats/tasks/{task_id}`
  - 查詢任務狀態與結果：
    ```json
    { "task_id": "id", "status": "PENDING|RUNNING|FINISHED|FAILURE", "result": null|object }
    ```
- GET `/stats/user/all_fcs_info`（需登入）
  - 回傳使用者所有 FCS 檔案的摘要資訊
- GET `/stats/user/files_statistics`（需登入）
  - 回傳使用者檔案統計（總數/總大小）

