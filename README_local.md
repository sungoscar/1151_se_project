# 管院空間管理系統

軟體工程學期專案，共有三個模組，每人負責一個：

| 模組 | 資料夾 | 網址前綴 |
|---|---|---|
| 共用資料（帳號註冊、審核、登入、登出） | `core/`、`www/common/` | `/api/auth` |
| 管院空間查詢模組 | `modules/space/`、`www/space/` | `/api/space` |
| 空間/物品預約借用模組 | `modules/booking/`、`www/booking/` | `/api/booking` |
| 志願排課模組 | `modules/course/`、`www/course/` | `/api/course` |

---

## 一、使用技術

| 部分 | 技術 |
|---|---|
| 專案管理 | uv（Python 3.12） |
| 後端 | FastAPI |
| 資料庫 | PostgreSQL（透過 psycopg 3 連線） |
| 登入狀態 | Session（`SessionMiddleware`，資料加上簽章後存在 cookie） |
| 前端 | HTML、CSS、JavaScript（`fetch` 呼叫 API，無使用框架） |

---

## 二、安裝與執行

### 1. 安裝 PostgreSQL

到 https://www.postgresql.org/download/ 下載安裝。安裝時設定的 `postgres` 密碼要記住。

### 2. 建立資料庫

開啟 pgAdmin 或 SQL Shell (psql)，執行：

```sql
CREATE DATABASE ibs_system;
```

### 3. 設定連線

複製 `.env.example` 並改名為 `.env`，把密碼改成自己的：

```
DATABASE_URL=postgresql://postgres:你的密碼@localhost:5432/ibs_system
```

`.env` 不會進 git，每個人各自設定。

### 4. 安裝套件並啟動

```bash
uv sync
uv run fastapi dev main.py
```

第一次啟動會自動建立資料表和測試資料。

### 5. 開啟網頁

| 網址 | 說明 |
|---|---|
| http://127.0.0.1:8000 | 系統首頁 |
| http://127.0.0.1:8000/docs | FastAPI 自動產生的 API 測試頁 |

### 6. 重設資料庫

刪除所有資料表（包含各模組的表），再重新建立測試資料：

```bash
uv run python -m core.database reset
```

修改了資料表欄位之後，要執行這個指令才會生效。

---

## 三、測試帳號

密碼都是 `1234`。

| 帳號 | 姓名 | 身分 | 狀態 | 用途 |
|---|---|---|---|---|
| admin | 系統管理員 | 管理員 | 已啟用 | |
| teacher1 | 王老師 | 老師 | 已啟用 | |
| student1 | 林同學 | 學生 | 已啟用 | |
| student2 | 陳同學 | 學生 | 已啟用 | |
| pending1 | 張同學 | 學生 | 待審核 | 展示帳號審核 |
| rejected1 | 李同學 | 老師 | 已退件 | 展示退件後重新申請 |

測試空間：203 教室（40 人）、204 教室（40 人）、441 教室（10 人）、443 教室（12 人）

---

## 四、專案結構

```
ibs_system/
├── main.py                 # 主程式：建表、session、掛上所有 API、開放網頁
├── pyproject.toml          # 專案設定與套件清單
├── .env.example            # 資料庫連線設定範本（複製成 .env）
├── core/                   # 共用資料（後端）
│   ├── config.py           # 設定值：連線字串、session 金鑰、是否開放註冊
│   ├── database.py         # 資料庫連線、users/spaces 建表、預設資料
│   ├── auth.py             # 權限檢查：get_current_user、check_login、check_role
│   └── router.py           # 帳號 API（/api/auth）
├── modules/                # 各模組（後端）
│   ├── space/    router.py、db.py
│   ├── booking/  router.py、db.py
│   └── course/   router.py、db.py
└── www/                    # 前端網頁
    ├── index.html/css/js   # 首頁
    ├── common/             # 共用資料（前端）
    │   ├── common.css      # 共用樣式
    │   ├── common.js       # 共用函式
    │   ├── login.*         # 登入、重新申請
    │   ├── register.*      # 申請帳號
    │   └── admin_users.*   # 帳號管理（管理員）
    ├── space/              # 空間查詢模組的頁面
    ├── booking/            # 預約借用模組的頁面
    └── course/             # 排課模組的頁面
```

---

## 五、帳號功能

### 帳號狀態流程

```
 申請帳號 ──▶ 待審核 ──核准（管理員）──▶ 已啟用（可以登入）
               ▲  │
               │  └──退件（管理員，填寫原因）──▶ 已退件
               │                                   │
               └──── 修改姓名或身分後重新申請 ────────┘
```

- 學生、老師可以自行申請帳號，身分自己選擇；管理員核准時可以更正身分
- 被退件的帳號登入時會看到退件原因，可以修改後重新申請
- 管理員也可以直接新增帳號（包含管理員帳號），建立後即可登入
- 管理員帳號不能自行申請

### 關閉自行註冊

如果之後改成「帳號一律由管理員新增」，把 `core/config.py` 的設定改成：

```python
ALLOW_SELF_REGISTER = False
```

註冊 API 會關閉，導覽列和登入頁的「註冊」連結也會自動隱藏。

### 權限等級

| 等級 | 說明 | 後端寫法 |
|---|---|---|
| 公開 | 不用登入 | `get_current_user(request)`（未登入時是 `None`） |
| 已登入 | 老師、學生、管理員 | `check_login(request)` |
| 限定角色 | 例如只有管理員 | `check_role(request, "admin")` |
| 多個角色 | 例如老師或管理員 | `check_role(request, "teacher", "admin")` |

---

## 六、資料庫設計（共用資料表）

### users（使用者）

| 欄位 | 型態 | 說明 |
|---|---|---|
| id | INTEGER | 主鍵，自動編號 |
| username | VARCHAR(20) | 帳號，不可重複，4～20 碼英文或數字 |
| password | TEXT | 密碼，至少 4 碼 |
| name | TEXT | 姓名 |
| role | TEXT | `student` 學生 / `teacher` 老師 / `admin` 管理員 |
| status | TEXT | `pending` 待審核 / `active` 已啟用 / `rejected` 已退件 |
| review_comment | TEXT | 退件原因 |
| reviewed_at | TIMESTAMP | 最後審核時間 |
| created_at | TIMESTAMP | 申請時間 |

### spaces（空間）

目前只有基本欄位，其餘欄位待組員確認後補上。查詢模組負責增刪修，借用與排課模組只讀。

| 欄位 | 型態 | 說明 |
|---|---|---|
| id | INTEGER | 主鍵，自動編號 |
| code | TEXT | 教室編號，不可重複 |
| name | TEXT | 顯示名稱 |
| capacity | INTEGER | 容納人數 |

---

## 七、帳號 API（`/api/auth`）

| 方法 | 網址 | 權限 | 參數 | 功能 |
|---|---|---|---|---|
| GET | `/config` | 公開 | | 是否開放自行註冊 |
| POST | `/register` | 公開 | username, password, name, role | 申請帳號（身分只能是學生或老師） |
| POST | `/login` | 公開 | username, password | 登入 |
| POST | `/reapply` | 被退件者 | username, password, name, role | 重新申請 |
| POST | `/logout` | 已登入 | | 登出 |
| GET | `/me` | 已登入 | | 目前登入者 |
| GET | `/users` | 管理員 | status（選填） | 帳號清單 |
| POST | `/users` | 管理員 | username, password, name, role | 直接新增帳號 |
| POST | `/users/{id}/approve` | 管理員 | role（選填） | 核准，可更正身分 |
| POST | `/users/{id}/reject` | 管理員 | comment | 退件，原因必填 |

登入時帳號狀態不是「已啟用」，會回傳 403，`detail` 是物件：

```json
{ "message": "帳號審核中，請等候管理員審核", "status": "pending" }
{ "message": "帳號申請未通過審核", "status": "rejected", "comment": "退件原因", "name": "...", "role": "..." }
```

### 錯誤代碼

| 代碼 | 意義 |
|---|---|
| 400 | 資料有誤，或狀態不允許此操作 |
| 401 | 尚未登入 |
| 403 | 已登入但沒有權限；或帳號還不能登入（待審核、已退件） |
| 404 | 找不到資料 |

---

## 八、各模組開發約定

### 後端

1. 只修改自己的 `modules/xxx/` 資料夾，**不需要修改 `main.py`**，router 已經接好
2. API 寫在 `router.py`，網址會自動加上 `/api/模組名` 前綴
3. 資料表寫在 `db.py` 的 `create_tables()`，測試資料寫在 `insert_test_data()`
4. 資料表名稱加上模組前綴，例如 `booking_xxx`
5. 共用資料表 `users`、`spaces` 只能用外鍵參照，要修改欄位請先和組員討論
6. 資料庫連線：

```python
from core.database import get_connection

with get_connection() as conn:          # 結束時自動 commit 並關閉連線
    rows = conn.execute(
        "SELECT * FROM spaces WHERE id = %s",   # PostgreSQL 佔位符號是 %s
        (space_id,),
    ).fetchall()
```

7. 所有 SQL 都用 `%s` 佔位符號傳入資料，不要用字串相加，防止 SQL Injection

### 前端

1. 頁面放在 `www/模組名/`，入口是 `index.html`（導覽列連到這裡）
2. 先引入共用檔案，再引入自己的檔案：

```html
<link rel="stylesheet" href="/common/common.css">
<link rel="stylesheet" href="/booking/booking.css">
...
<script src="/common/common.js"></script>
<script src="/booking/booking.js"></script>
```

3. `common.js` 提供的函式：

| 函式 | 用途 |
|---|---|
| `renderNavbar()` | 產生導覽列，回傳目前登入者（未登入時是 `null`） |
| `requireLogin(roles)` | 需要登入的頁面使用；未登入會跳到登入頁，登入後自動回來 |
| `goToLogin()` | 跳到登入頁，登入後回到目前頁面（例如未登入按下「申請借用」） |
| `api(url, { method, data })` | 呼叫 API，`data` 會以表單格式送出；失敗時丟出錯誤，`error.message` 是訊息 |
| `escapeHtml(text)` | 用 `innerHTML` 顯示使用者輸入的內容前，一定要先經過這個函式 |
| `showMessage(element, text, type)` | 顯示訊息，`type` 可以是 `error`、`success`、`info` |
| `ROLE_NAMES`、`STATUS_NAMES` | 角色、帳號狀態的中文名稱 |

4. `common.css` 提供的樣式：`.container`、`.card`、`.btn`（`.btn-secondary`、`.btn-danger`、`.btn-small`）、`.form-group`、`.table`、`.message`、`.tag`、`.tabs`、`.hidden`

### 日期與時間格式

| 類型 | 格式 |
|---|---|
| 日期 | `YYYY-MM-DD` |
| 時間 | `HH:MM` |
| 日期時間 | `YYYY-MM-DD HH:MM:SS` |

資料庫連線固定使用台灣時區（Asia/Taipei）。

---

## 九、Git 流程

1. 共用資料完成後 commit 到 `main`
2. 每個人從 `main` 開自己的分支：`feature/space`、`feature/booking`、`feature/course`
3. 每完成一個小功能就發 Pull Request，請另一位組員看過再合併
4. 要修改共用資料（`core/`、`www/common/`）時，另開 `feature/core-xxx` 分支，三人確認後再合併
5. 定期把 `main` 的更新合併到自己的分支：`git merge main`

---

## 十、安全性設計

- **防止 SQL Injection**：所有 SQL 都使用 `%s` 佔位符號傳入資料
- **防止 XSS**：前端用 `innerHTML` 顯示使用者輸入的內容前，都先經過 `escapeHtml()`
- **身分驗證**：使用者身分存在 session 中，由 `itsdangerous` 加上簽章，無法自行竄改
- **權限控制**：後端每支需要權限的 API 都用 `check_login()` 或 `check_role()` 檢查，不只依賴前端隱藏按鈕
- **自行註冊的身分限制**：後端只接受學生或老師，無法透過 API 把自己註冊成管理員
- **登入後跳轉**：`?next=` 只接受站內路徑，避免被導到其他網站

> 本專題為課堂作業，密碼以明文儲存、session 金鑰寫在程式中。正式上線時應將密碼雜湊後儲存，金鑰改用環境變數設定。

---

## 十一、測試流程（共用資料）

1. 首頁未登入 → 導覽列顯示「登入」「註冊」
2. 未登入直接開啟 `/common/admin_users.html` → 跳到登入頁
3. 申請帳號（選老師）→ 顯示「申請已送出」
4. 用剛申請的帳號登入 → 顯示「帳號審核中」
5. 以 `admin` 登入 → 帳號管理的待審核清單出現該帳號
6. 退件並填寫原因 → 狀態變為「已退件」
7. 用該帳號登入 → 顯示退件原因與重新申請表單，改成學生後重新送出
8. 以 `admin` 核准 → 該帳號可以登入，導覽列顯示「姓名（學生）」
9. 以 `admin` 新增一個帳號 → 不需審核就可以登入
10. 以 `student1` 登入後開啟帳號管理頁 → 顯示沒有權限並跳回首頁
