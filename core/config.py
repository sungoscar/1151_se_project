# ==========================================================
# core/config.py（共用資料）
# 功能：整個系統共用的設定值
#   - DATABASE_URL：PostgreSQL 連線字串
#   - SECRET_KEY：session cookie 的簽章金鑰
#   - ALLOW_SELF_REGISTER：是否開放學生、老師自行註冊
# ==========================================================

import os
from pathlib import Path

# 專案根目錄（core 資料夾的上一層）
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------
# 讀取專案根目錄的 .env 檔案
# 每個組員電腦上的 PostgreSQL 密碼可能不同，
# 所以連線字串寫在 .env（不進 git），而不是寫死在程式裡
# 格式：每行一個「名稱=值」，# 開頭為註解
# ----------------------------------------------------------
def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line == "" or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # setdefault：如果系統環境變數已經有設定，以環境變數為準
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()

# PostgreSQL 連線字串，沒有 .env 時使用預設值
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ibs_system",
)

# session 簽章金鑰（課堂作業寫在程式中；正式上線應改用環境變數）
SECRET_KEY = os.environ.get("SECRET_KEY", "ibs-system-secret-key")

# 是否開放自行註冊
# True ：學生、老師可自行申請帳號，由管理員審核
# False：關閉自行註冊，帳號一律由管理員新增
ALLOW_SELF_REGISTER = True

# 角色與帳號狀態（其他檔案檢查資料時共用，避免各自寫不同的字）
ROLES = ("student", "teacher", "admin")
SELF_REGISTER_ROLES = ("student", "teacher")   # 自行註冊只能選這兩種
STATUSES = ("pending", "active", "rejected")
