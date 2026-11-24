# ==========================================================
# main.py
# 功能：FastAPI 主程式
#   1. 初始化資料庫（先建共用資料表，再建各模組的表）
#   2. 加入 session 功能
#   3. 掛上共用帳號 API 與三個模組的 API
#   4. 開放 www 資料夾的網頁
# 執行方式：uv run fastapi dev main.py
#
# 各模組只需要修改自己的 modules/xxx 與 www/xxx 資料夾，不需要修改這個檔案
# ==========================================================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from core import router as auth
from core.config import BASE_DIR, SECRET_KEY
from core.database import init_db
from modules.booking import db as booking_db
from modules.booking import router as booking
from modules.course import db as course_db
from modules.course import router as course
from modules.space import db as space_db
from modules.space import router as space

# ----------------------------------------------------------
# 1. 初始化資料庫
# 順序很重要：各模組的資料表會用外鍵參照 users、spaces，
# 所以共用資料表一定要先建立
# ----------------------------------------------------------
init_db()

for module_db in (space_db, booking_db, course_db):
    module_db.create_tables()
    module_db.insert_test_data()

# ----------------------------------------------------------
# 2. 建立 app 並加入 session
# ----------------------------------------------------------
app = FastAPI(title="管院空間管理系統")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# ----------------------------------------------------------
# 3. 掛上 API
# ----------------------------------------------------------
app.include_router(auth.router)       # /api/auth
app.include_router(space.router)      # /api/space
app.include_router(booking.router)    # /api/booking
app.include_router(course.router)     # /api/course

# ----------------------------------------------------------
# 4. 開放網頁（一定要放在最後，否則會擋住上面的 API）
# html=True：網址是資料夾時自動顯示 index.html，例如 / → www/index.html
# ----------------------------------------------------------
app.mount("/", StaticFiles(directory=BASE_DIR / "www", html=True), name="www")
