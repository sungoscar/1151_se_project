# ==========================================================
# modules/space/router.py
# 功能：空間查詢模組的 API（空殼，由負責的組員填入內容）
#
# 約定：
#   - 網址一律以 /api/space 開頭（由下面的 prefix 自動加上）
#   - 權限檢查使用 core.auth 的 get_current_user / check_login / check_role
#   - 資料庫連線使用 core.database 的 get_connection，SQL 佔位符號用 %s
#   - 不需要修改 main.py，這個 router 已經接好了
# ==========================================================

from fastapi import APIRouter

router = APIRouter(prefix="/api/space", tags=["空間查詢模組"])
