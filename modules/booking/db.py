# ==========================================================
# modules/booking/db.py
# 功能：空間/物品預約借用模組自己的資料表與測試資料（空殼，由負責的組員填入內容）
#
# 約定：
#   - 資料表名稱加上前綴 booking_，例如 booking_xxx
#   - 共用資料表 users、spaces 由 core/database.py 建立，這裡只能用外鍵參照，不要修改
#   - main.py 啟動時會依序呼叫 create_tables()、insert_test_data()
#     （一定在共用資料表建立之後才呼叫）
#
# 範例：
#   from core.database import get_connection
#
#   def create_tables():
#       with get_connection() as conn:
#           conn.execute("""
#               CREATE TABLE IF NOT EXISTS booking_example (
#                   id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
#                   user_id INTEGER NOT NULL REFERENCES users(id)
#               )
#           """)
# ==========================================================


def create_tables():
    pass


def insert_test_data():
    pass
