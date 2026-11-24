下面是共用部分的完整規格。你確認後，我就照最後的實作順序，一次寫一個檔案給你確認。

---

# 共用部分規格

## 一、專案結構

```
project/
├── main.py                  # 建立 app、session、建表、掛 router、開放 www
├── pyproject.toml           # fastapi[standard]、itsdangerous、python-multipart
├── .gitignore               # .venv/、__pycache__/、app.db
├── README.md
├── core/
│   ├── __init__.py
│   ├── config.py            # 設定值
│   ├── database.py          # 連線、建 users/spaces、預設資料
│   ├── auth.py              # 權限檢查函式
│   └── router.py            # /api/auth
├── modules/
│   ├── __init__.py
│   ├── space/   (__init__.py, router.py, db.py)
│   ├── booking/ (__init__.py, router.py, db.py)
│   └── course/  (__init__.py, router.py, db.py)
└── www/
    ├── index.html  index.css  index.js
    ├── common/
    │   ├── common.css  common.js
    │   ├── login.html  login.css  login.js
    │   ├── register.html  register.css  register.js
    │   └── admin_users.html  admin_users.css  admin_users.js
    ├── space/   booking/   course/        # 各組員自己的頁面
```

**模組空殼**：三個模組的 `router.py`、`db.py` 先由你建成空殼，`main.py` 也預先接好三個模組。組員只要往自己的資料夾裡填內容，完全不用動 `main.py`，合併時就不會衝突。

## 二、`core/config.py`

| 設定 | 值 | 說明 |
|---|---|---|
| `DB_NAME` | `"app.db"` | 資料庫檔名 |
| `SECRET_KEY` | 一段字串 | session 簽章（作業用，寫在程式裡） |
| `ALLOW_SELF_REGISTER` | `True` | `False` 時關閉自行註冊 |

## 三、資料表（`core/database.py`）

**users**

| 欄位 | 型態 | 說明 |
|---|---|---|
| id | INTEGER PK | 自動編號 |
| username | TEXT UNIQUE NOT NULL | 帳號 |
| password | TEXT NOT NULL | 密碼（作業用明文） |
| name | TEXT NOT NULL | 姓名 |
| role | TEXT NOT NULL | `student` / `teacher` / `admin` |
| status | TEXT NOT NULL | `pending` / `active` / `rejected` |
| review_comment | TEXT DEFAULT '' | 退件原因 |
| reviewed_at | TEXT | 最後審核時間 |
| created_at | TEXT NOT NULL | 申請時間 |

**spaces**（基本版，其他欄位等和組員確認後再補）

| 欄位 | 型態 | 說明 |
|---|---|---|
| id | INTEGER PK | 自動編號 |
| code | TEXT UNIQUE NOT NULL | 教室編號 |
| name | TEXT NOT NULL | 顯示名稱 |
| capacity | INTEGER NOT NULL | 容納人數 |

**函式**：`get_connection()`、`create_tables()`、`insert_default_data()`、`init_db()`

**預設資料**（只在資料表是空的時候放入）

| 帳號 | 密碼 | 姓名 | 角色 | 狀態 |
|---|---|---|---|---|
| admin | 1234 | 系統管理員 | admin | active |
| teacher1 | 1234 | 王老師 | teacher | active |
| student1 | 1234 | 林同學 | student | active |
| student2 | 1234 | 陳同學 | student | active |
| pending1 | 1234 | 張同學 | student | pending |
| rejected1 | 1234 | 李同學 | teacher | rejected（原因：身分不符，請確認） |

空間：203 教室（40 人）、204 教室（40 人）、441 教室（10 人）、443 教室（12 人）

## 四、權限函式（`core/auth.py`）

| 函式 | 行為 |
|---|---|
| `get_current_user(request)` | 有登入回傳 `{id, name, role}`，沒登入回傳 `None` |
| `check_login(request)` | 沒登入丟 401「請先登入」 |
| `check_role(request, *roles)` | 角色不符丟 403「沒有權限使用此功能」 |

session 只存 `user_id`、`name`、`role`。

## 五、帳號 API（`core/router.py`，前綴 `/api/auth`）

| 方法 | 網址 | 權限 | 參數 | 功能 |
|---|---|---|---|---|
| GET | `/config` | 公開 | － | 回傳是否開放自行註冊，前端用來決定要不要顯示「註冊」 |
| POST | `/register` | 公開 | username, password, name, role | 自行註冊，狀態為 pending |
| POST | `/login` | 公開 | username, password | 登入 |
| POST | `/reapply` | 被退件者 | username, password, name, role | 重新申請，狀態回到 pending |
| POST | `/logout` | 已登入 | － | 登出 |
| GET | `/me` | 已登入 | － | 目前登入者 |
| GET | `/users` | 管理員 | status（選填） | 帳號清單 |
| POST | `/users` | 管理員 | username, password, name, role | 直接建立帳號，狀態為 active |
| POST | `/users/{id}/approve` | 管理員 | role（選填，用來更正身分） | 核准 |
| POST | `/users/{id}/reject` | 管理員 | comment（必填） | 退件 |

**驗證規則與訊息**

| 情況 | 代碼 | 訊息 |
|---|---|---|
| 帳號不是 3～20 碼英文或數字 | 400 | 帳號須為 3～20 碼英文或數字 |
| 密碼少於 4 碼 | 400 | 密碼至少 4 碼 |
| 姓名空白 | 400 | 請填寫姓名 |
| 自行註冊、重新申請時身分不是學生或老師 | 400 | 身分只能選擇學生或老師 |
| 帳號重複 | 400 | 此帳號已被使用 |
| 關閉自行註冊時呼叫 `/register` | 403 | 目前不開放自行註冊 |
| 帳號或密碼錯誤 | 400 | 帳號或密碼錯誤 |
| 登入時狀態為 pending | 403 | 帳號審核中，請等候管理員審核 |
| 登入時狀態為 rejected | 403 | 回傳 `{status: "rejected", comment: 退件原因}`，前端顯示重新申請表單 |
| 對非 rejected 的帳號重新申請 | 400 | 此帳號不需要重新申請 |
| 審核非 pending 的帳號 | 400 | 此帳號不是待審核狀態 |
| 退件未填原因 | 400 | 請填寫退件原因 |

管理員帳號只能由預設資料或其他管理員建立（`POST /users` 可以建立 admin）。

## 六、`main.py`

1. 呼叫 `init_db()` 建共用表，再依序呼叫三個模組的 `create_tables()`、`insert_test_data()`
2. 加入 `SessionMiddleware`
3. `include_router`：auth、space、booking、course
4. `/` 導向 `/index.html`
5. 最後 mount `www`

## 七、前端共用

**`common.js`**

| 函式 | 功能 |
|---|---|
| `escapeHtml(text)` | 防 XSS |
| `api(url, options)` | 包裝 `fetch`；失敗時丟出含 `detail` 的錯誤，讓頁面顯示訊息 |
| `getCurrentUser()` | 取得登入者，未登入時回傳 `null` |
| `requireLogin(roles)` | 需要登入的頁面使用；未登入時跳到 `login.html?next=目前頁面`，角色不符時跳回首頁 |
| `renderNavbar()` | 在頁面最上方產生導覽列 |

**導覽列**：系統名稱（連到首頁）、空間查詢、預約借用、排課；右側未登入時顯示「登入」和「註冊」（關閉自行註冊時不顯示註冊），登入後顯示「姓名（身分）」和「登出」，管理員多一個「帳號管理」。

**`common.css`**：配色變數、導覽列、按鈕（主要、次要、危險）、表格、表單、訊息框、狀態標籤（待審核、已通過、已退件）。

**頁面**

| 頁面 | 內容 |
|---|---|
| `index.html` | 公開首頁：三個模組的入口卡片 |
| `login.html` | 登入表單；登入成功後回到 `next` 指定的頁面（沒有的話回首頁）；被退件時顯示退件原因和重新申請表單（姓名、身分、密碼） |
| `register.html` | 註冊表單（帳號、密碼、確認密碼、姓名、身分）；送出後顯示「申請已送出，請等候管理員審核」 |
| `admin_users.html` | 限管理員。分頁：待審核（核准時可改身分、退件時要填原因）、全部帳號（可依狀態篩選）、新增帳號 |

## 八、實作順序（每一步給你確認後再做下一步）

1. 專案初始化：`pyproject.toml`、`.gitignore`、資料夾與 `__init__.py`
2. `core/config.py`、`core/database.py`
3. `core/auth.py`
4. `core/router.py`（帳號 API，用 `/docs` 測試）
5. 三個模組空殼和 `main.py`
6. `common.css`、`common.js`
7. `index`、`login`、`register`、`admin_users` 頁面
8. `README.md`，整體測一次後 commit 到 main

---

有兩點想先跟你確認：

1. 帳號規則（3～20 碼英文或數字、密碼至少 4 碼）可以嗎？
2. 專案名稱和系統名稱要用什麼？例如資料夾叫 `ibs_space_system`，頁面標題叫「管院空間管理系統」。

這兩點確認後就從第 1 步開始。這份規格之後也要給組員看，需要的話我可以整理成一份文件。
