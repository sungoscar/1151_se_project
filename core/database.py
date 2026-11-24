# ==========================================================
# core/database.py（共用資料）
# 功能：負責所有模組共用的資料庫工作
#   1. 取得資料庫連線（get_connection）
#   2. 建立共用資料表 users、spaces（create_tables）
#   3. 放入預設帳號與測試空間（insert_default_data）
# 使用的資料庫：PostgreSQL（透過 psycopg 3 連線）
#
# 各模組使用方式：
#   from core.database import get_connection
#   with get_connection() as conn:
#       rows = conn.execute("SELECT * FROM spaces WHERE id = %s", (space_id,)).fetchall()
#
# 注意：PostgreSQL 的佔位符號是 %s（SQLite 是 ?）
# ==========================================================

import sys

import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL


# ----------------------------------------------------------
# 取得資料庫連線
# 搭配 with 使用：
#   - 區塊正常結束 → 自動 commit 並關閉連線
#   - 區塊中發生錯誤 → 自動 rollback 並關閉連線
# row_factory=dict_row：查詢結果可以用欄位名稱取值，例如 row["name"]
# options：連線時固定使用台灣時區，每個組員電腦的時區設定不同，時間也會一致
# ----------------------------------------------------------
def get_connection():
    try:
        return psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
            options="-c timezone=Asia/Taipei",
        )
    except psycopg.OperationalError as error:
        raise RuntimeError(
            "無法連線到 PostgreSQL，請確認：\n"
            "  1. PostgreSQL 服務已啟動\n"
            "  2. 已建立資料庫（例如 ibs_system）\n"
            "  3. .env 裡的 DATABASE_URL 帳號、密碼正確\n"
            f"目前的連線字串：{DATABASE_URL}"
        ) from error


# ----------------------------------------------------------
# 建立共用資料表：users、spaces
# 使用 IF NOT EXISTS：表已經存在就跳過，不會清空資料
# 注意：表建好之後再修改欄位不會自動生效，要先執行重設（見最下方）
# ----------------------------------------------------------
def create_tables():
    with get_connection() as conn:
        # 表 1：users（使用者，三個模組共用）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                username       VARCHAR(20) NOT NULL UNIQUE,   -- 帳號
                password       TEXT NOT NULL,                 -- 密碼（作業用，明文儲存）
                name           TEXT NOT NULL,                 -- 姓名
                role           TEXT NOT NULL
                               CHECK (role IN ('student', 'teacher', 'admin')),
                status         TEXT NOT NULL DEFAULT 'pending'
                               CHECK (status IN ('pending', 'active', 'rejected')),
                review_comment TEXT NOT NULL DEFAULT '',      -- 退件原因
                reviewed_at    TIMESTAMP(0),                  -- 最後審核時間
                created_at     TIMESTAMP(0) NOT NULL DEFAULT LOCALTIMESTAMP(0)  -- 申請時間
            )
        """)

        # 表 2：spaces（空間，查詢模組負責增刪修，借用與排課模組只讀）
        # 目前只有基本欄位，其他欄位等組員確認後再加
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spaces (
                id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                code     TEXT NOT NULL UNIQUE,    -- 教室編號，例如 203
                name     TEXT NOT NULL,           -- 顯示名稱
                capacity INTEGER NOT NULL CHECK (capacity > 0)  -- 容納人數
            )
        """)


# ----------------------------------------------------------
# 放入預設帳號與測試空間
# ON CONFLICT DO NOTHING：資料已經存在就跳過，重複啟動也不會重複新增
# ----------------------------------------------------------
def insert_default_data():
    # 每一筆依序是：(帳號, 密碼, 姓名, 角色, 狀態, 退件原因)
    default_users = [
        ("admin",     "1234", "系統管理員", "admin",   "active",   ""),
        ("teacher1",  "1234", "王老師",     "teacher", "active",   ""),
        ("student1",  "1234", "林同學",     "student", "active",   ""),
        ("student2",  "1234", "陳同學",     "student", "active",   ""),
        ("pending1",  "1234", "張同學",     "student", "pending",  ""),
        ("rejected1", "1234", "李同學",     "teacher", "rejected", "身分不符，請確認"),
    ]

    # 每一筆依序是：(教室編號, 名稱, 容納人數)
    default_spaces = [
        ("203", "203 教室", 40),
        ("204", "204 教室", 40),
        ("441", "441 教室", 10),
        ("443", "443 教室", 12),
    ]

    with get_connection() as conn:
        for user in default_users:
            conn.execute(
                """
                INSERT INTO users (username, password, name, role, status, review_comment)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
                user,
            )

        # 被退件的預設帳號補上審核時間，畫面上才看得出「已審核過」
        conn.execute("""
            UPDATE users SET reviewed_at = LOCALTIMESTAMP(0)
            WHERE username = 'rejected1' AND reviewed_at IS NULL
        """)

        for space in default_spaces:
            conn.execute(
                """
                INSERT INTO spaces (code, name, capacity)
                VALUES (%s, %s, %s)
                ON CONFLICT (code) DO NOTHING
                """,
                space,
            )


# ----------------------------------------------------------
# 初始化共用資料：建表 + 放預設資料
# main.py 啟動時會呼叫，而且一定要在各模組建表之前
# （各模組的資料表會用外鍵參照 users、spaces）
# ----------------------------------------------------------
def init_db():
    create_tables()
    insert_default_data()


# ----------------------------------------------------------
# 重設資料庫：刪除所有資料表（包含各模組的表），回到初始狀態
# 只在開發時使用，執行方式：uv run python -m core.database reset
# ----------------------------------------------------------
def reset_db():
    with get_connection() as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")


# ----------------------------------------------------------
# 直接執行這個檔案時：
#   uv run python -m core.database        → 初始化並列出資料
#   uv run python -m core.database reset  → 刪除所有資料表後重新初始化
# ----------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        answer = input("確定要刪除資料庫中所有資料表嗎？（輸入 yes 確認）：")
        if answer != "yes":
            print("已取消")
            sys.exit()
        reset_db()
        print("已刪除所有資料表")

    init_db()

    with get_connection() as conn:
        print("=== users ===")
        for user in conn.execute("SELECT * FROM users ORDER BY id").fetchall():
            print(user["id"], user["username"], user["name"], user["role"], user["status"])

        print("=== spaces ===")
        for space in conn.execute("SELECT * FROM spaces ORDER BY id").fetchall():
            print(space["id"], space["code"], space["name"], space["capacity"])

    print("共用資料初始化完成！")
