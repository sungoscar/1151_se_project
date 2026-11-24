# ==========================================================
# core/router.py（共用資料）
# 功能：帳號相關 API，網址都以 /api/auth 開頭
#   - 註冊、登入、登出、重新申請
#   - 管理員：帳號清單、審核（核准／退件）、直接新增帳號
# ==========================================================

import re

from fastapi import APIRouter, Form, HTTPException, Request

from core.auth import check_login, check_role
from core.config import ALLOW_SELF_REGISTER, ROLES, SELF_REGISTER_ROLES, STATUSES
from core.database import get_connection

router = APIRouter(prefix="/api/auth", tags=["共用資料：帳號"])

# 帳號只能是 4～20 碼英文或數字
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9]{4,20}$")

# 查詢使用者時要回傳的欄位（不回傳密碼）
# to_char：把時間轉成「YYYY-MM-DD HH:MM:SS」字串，前端可以直接顯示
USER_COLUMNS = """
    id, username, name, role, status, review_comment,
    to_char(reviewed_at, 'YYYY-MM-DD HH24:MI:SS') AS reviewed_at,
    to_char(created_at,  'YYYY-MM-DD HH24:MI:SS') AS created_at
"""


# ==========================================================
# 共用的檢查函式
# ==========================================================

# ----------------------------------------------------------
# 檢查帳號、密碼、姓名、角色格式
# allowed_roles：允許的角色（自行註冊只能學生、老師；管理員新增可以三種）
# 格式正確時回傳去掉前後空白的姓名
# ----------------------------------------------------------
def validate_user_data(username: str, password: str, name: str, role: str, allowed_roles):
    if not USERNAME_PATTERN.match(username):
        raise HTTPException(status_code=400, detail="帳號須為 4～20 碼英文或數字")

    if len(password) < 4:
        raise HTTPException(status_code=400, detail="密碼至少 4 碼")

    name = name.strip()
    if name == "":
        raise HTTPException(status_code=400, detail="請填寫姓名")

    if role not in allowed_roles:
        if allowed_roles == SELF_REGISTER_ROLES:
            raise HTTPException(status_code=400, detail="身分只能選擇學生或老師")
        raise HTTPException(status_code=400, detail="身分不正確")

    return name


# ----------------------------------------------------------
# 用帳號和密碼查詢使用者，找不到時回傳 None
# ----------------------------------------------------------
def find_user_by_login(conn, username: str, password: str):
    return conn.execute(
        "SELECT * FROM users WHERE username = %s AND password = %s",
        (username, password),
    ).fetchone()


# ----------------------------------------------------------
# 新增使用者（自行註冊與管理員新增共用）
# 帳號重複時回傳 400
# ----------------------------------------------------------
def insert_user(username: str, password: str, name: str, role: str, status: str):
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = %s", (username,)
        ).fetchone()
        if exists is not None:
            raise HTTPException(status_code=400, detail="此帳號已被使用")

        conn.execute(
            """
            INSERT INTO users (username, password, name, role, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, password, name, role, status),
        )


# ----------------------------------------------------------
# 取得待審核的使用者，不是 pending 時回傳 400
# ----------------------------------------------------------
def get_pending_user(conn, user_id: int):
    user = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()

    if user is None:
        raise HTTPException(status_code=404, detail="找不到此帳號")
    if user["status"] != "pending":
        raise HTTPException(status_code=400, detail="此帳號不是待審核狀態")

    return user


# ==========================================================
# 公開 API
# ==========================================================

# ----------------------------------------------------------
# 系統設定：前端用來決定要不要顯示「註冊」
# ----------------------------------------------------------
@router.get("/config")
def get_config():
    return {"allow_self_register": ALLOW_SELF_REGISTER}


# ----------------------------------------------------------
# 自行註冊：學生、老師自己申請，狀態為 pending，等管理員審核
# ----------------------------------------------------------
@router.post("/register")
def register(
    username: str = Form(),
    password: str = Form(),
    name: str = Form(),
    role: str = Form(),
):
    if not ALLOW_SELF_REGISTER:
        raise HTTPException(status_code=403, detail="目前不開放自行註冊")

    name = validate_user_data(username, password, name, role, SELF_REGISTER_ROLES)
    insert_user(username, password, name, role, "pending")

    return {"message": "申請已送出，請等候管理員審核"}


# ----------------------------------------------------------
# 登入
# 成功：把使用者資料存進 session
# pending、rejected：回傳 403，detail 是物件，前端依 status 顯示不同畫面
# ----------------------------------------------------------
@router.post("/login")
def login(request: Request, username: str = Form(), password: str = Form()):
    with get_connection() as conn:
        user = find_user_by_login(conn, username, password)

    if user is None:
        raise HTTPException(status_code=400, detail="帳號或密碼錯誤")

    if user["status"] == "pending":
        raise HTTPException(status_code=403, detail={
            "message": "帳號審核中，請等候管理員審核",
            "status": "pending",
        })

    if user["status"] == "rejected":
        raise HTTPException(status_code=403, detail={
            "message": "帳號申請未通過審核",
            "status": "rejected",
            "comment": user["review_comment"],
            "name": user["name"],     # 讓重新申請表單預先填入原本的資料
            "role": user["role"],
        })

    # 登入成功：之後瀏覽器每次呼叫 API 都會自動帶著 session cookie
    request.session["user_id"] = user["id"]
    request.session["name"] = user["name"]
    request.session["role"] = user["role"]

    return {
        "message": "登入成功",
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
    }


# ----------------------------------------------------------
# 重新申請：被退件的帳號修改姓名或身分後再送出一次
# 被退件的帳號無法登入，所以要用帳號＋密碼確認是本人
# ----------------------------------------------------------
@router.post("/reapply")
def reapply(
    username: str = Form(),
    password: str = Form(),
    name: str = Form(),
    role: str = Form(),
):
    with get_connection() as conn:
        user = find_user_by_login(conn, username, password)
        if user is None:
            raise HTTPException(status_code=400, detail="帳號或密碼錯誤")
        if user["status"] != "rejected":
            raise HTTPException(status_code=400, detail="此帳號不需要重新申請")

        name = validate_user_data(username, password, name, role, SELF_REGISTER_ROLES)

        conn.execute(
            """
            UPDATE users
            SET name = %s, role = %s, status = 'pending', review_comment = ''
            WHERE id = %s
            """,
            (name, role, user["id"]),
        )

    return {"message": "已重新送出申請，請等候管理員審核"}


# ==========================================================
# 已登入 API
# ==========================================================

# ----------------------------------------------------------
# 登出：清空 session
# ----------------------------------------------------------
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "已登出"}


# ----------------------------------------------------------
# 取得目前登入者
# ----------------------------------------------------------
@router.get("/me")
def me(request: Request):
    return check_login(request)


# ==========================================================
# 管理員 API
# ==========================================================

# ----------------------------------------------------------
# 帳號清單，可用 status 篩選（pending / active / rejected）
# 不給 status 時列出全部
# ----------------------------------------------------------
@router.get("/users")
def list_users(request: Request, status: str | None = None):
    check_role(request, "admin")

    with get_connection() as conn:
        if status is None or status == "":
            rows = conn.execute(
                f"SELECT {USER_COLUMNS} FROM users ORDER BY created_at DESC, id DESC"
            ).fetchall()
        else:
            if status not in STATUSES:
                raise HTTPException(status_code=400, detail="狀態不正確")
            rows = conn.execute(
                f"SELECT {USER_COLUMNS} FROM users WHERE status = %s "
                "ORDER BY created_at DESC, id DESC",
                (status,),
            ).fetchall()

    return rows


# ----------------------------------------------------------
# 管理員直接新增帳號：狀態直接是 active，可以建立管理員帳號
# ----------------------------------------------------------
@router.post("/users")
def create_user(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    name: str = Form(),
    role: str = Form(),
):
    check_role(request, "admin")

    name = validate_user_data(username, password, name, role, ROLES)
    insert_user(username, password, name, role, "active")

    return {"message": "帳號已建立"}


# ----------------------------------------------------------
# 核准：pending → active
# role 選填：申請人選錯身分時，管理員可以順便更正
# ----------------------------------------------------------
@router.post("/users/{user_id}/approve")
def approve_user(request: Request, user_id: int, role: str | None = Form(None)):
    check_role(request, "admin")

    with get_connection() as conn:
        user = get_pending_user(conn, user_id)

        if role is None or role == "":
            role = user["role"]
        elif role not in SELF_REGISTER_ROLES:
            raise HTTPException(status_code=400, detail="身分只能選擇學生或老師")

        conn.execute(
            """
            UPDATE users
            SET status = 'active', role = %s, review_comment = '',
                reviewed_at = LOCALTIMESTAMP(0)
            WHERE id = %s
            """,
            (role, user_id),
        )

    return {"message": "已核准"}


# ----------------------------------------------------------
# 退件：pending → rejected，必須填寫原因
# 申請人登入時會看到原因，修改後可以重新申請
# ----------------------------------------------------------
@router.post("/users/{user_id}/reject")
def reject_user(request: Request, user_id: int, comment: str = Form("")):
    check_role(request, "admin")

    comment = comment.strip()
    if comment == "":
        raise HTTPException(status_code=400, detail="請填寫退件原因")

    with get_connection() as conn:
        get_pending_user(conn, user_id)
        conn.execute(
            """
            UPDATE users
            SET status = 'rejected', review_comment = %s,
                reviewed_at = LOCALTIMESTAMP(0)
            WHERE id = %s
            """,
            (comment, user_id),
        )

    return {"message": "已退件"}
