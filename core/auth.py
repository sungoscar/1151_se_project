# ==========================================================
# core/auth.py（共用資料）
# 功能：三個模組共用的登入狀態與權限檢查
#
# 各模組使用方式：
#   from core.auth import get_current_user, check_login, check_role
#
#   @router.get("/public")             # 公開：不用登入
#   def public_api(request: Request):
#       user = get_current_user(request)   # 沒登入時是 None
#
#   @router.post("/something")         # 需要登入
#   def api(request: Request):
#       user = check_login(request)
#
#   @router.post("/admin-only")        # 限定角色（可以傳多個）
#   def api(request: Request):
#       user = check_role(request, "admin")
#       user = check_role(request, "teacher", "admin")
# ==========================================================

from fastapi import HTTPException, Request


# ----------------------------------------------------------
# 取得目前登入者
# 已登入：回傳 {"id", "name", "role"}
# 未登入：回傳 None（不丟錯誤，給「公開但登入後顯示更多」的 API 使用）
# ----------------------------------------------------------
def get_current_user(request: Request):
    user_id = request.session.get("user_id")

    if user_id is None:
        return None

    return {
        "id": user_id,
        "name": request.session.get("name"),
        "role": request.session.get("role"),
    }


# ----------------------------------------------------------
# 檢查是否已登入
# 未登入：丟出 401，API 會直接停止
# ----------------------------------------------------------
def check_login(request: Request):
    user = get_current_user(request)

    if user is None:
        raise HTTPException(status_code=401, detail="請先登入")

    return user


# ----------------------------------------------------------
# 檢查是否已登入，而且角色符合其中一個
# 例如 check_role(request, "teacher", "admin")：老師或管理員都可以
# 角色不符：丟出 403（已登入但沒有權限）
# ----------------------------------------------------------
def check_role(request: Request, *roles: str):
    user = check_login(request)

    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="沒有權限使用此功能")

    return user
