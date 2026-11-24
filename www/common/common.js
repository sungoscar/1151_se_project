// ==========================================================
// www/common/common.js（共用資料）
// 三個模組共用的前端函式
//   escapeHtml()      防止 XSS
//   api()             呼叫後端 API，統一處理錯誤
//   getCurrentUser()  取得目前登入者（未登入時回傳 null）
//   requireLogin()    需要登入的頁面使用
//   renderNavbar()    產生導覽列
//   showMessage()     顯示訊息
// 各模組頁面先引入這個檔案，再引入自己的 JS
// ==========================================================

// 角色與狀態的中文名稱
const ROLE_NAMES = {
    student: "學生",
    teacher: "老師",
    admin: "管理員",
};

const STATUS_NAMES = {
    pending: "待審核",
    active: "已啟用",
    rejected: "已退件",
};

// 導覽列的模組連結（新增模組時在這裡加一行）
const NAV_LINKS = [
    { text: "空間查詢", href: "/space/" },
    { text: "預約借用", href: "/booking/" },
    { text: "排課", href: "/course/" },
];


// ----------------------------------------------------------
// 把使用者輸入的特殊符號轉成安全的文字，防止 XSS
// 用 innerHTML 顯示任何使用者輸入的內容前，一定要先經過這個函式
// ----------------------------------------------------------
function escapeHtml(text) {
    if (text === null || text === undefined) {
        return "";
    }
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}


// ----------------------------------------------------------
// 呼叫後端 API
// url：API 網址，例如 "/api/auth/me"
// options：
//   method：預設 GET
//   data：要送出的資料（物件），會轉成表單格式送出，後端用 Form() 接收
// 成功：回傳後端的 JSON
// 失敗：丟出錯誤，error.message 是錯誤訊息，error.status 是狀態碼，
//       error.detail 是後端回傳的完整 detail（有些 API 會回傳物件）
// ----------------------------------------------------------
async function api(url, options = {}) {
    const fetchOptions = {
        method: options.method || "GET",
    };

    if (options.data) {
        const formData = new FormData();
        for (const [key, value] of Object.entries(options.data)) {
            if (value !== null && value !== undefined) {
                formData.append(key, value);
            }
        }
        fetchOptions.body = formData;
    }

    const response = await fetch(url, fetchOptions);

    // 有些錯誤（例如伺服器當機）不會回傳 JSON，所以要先判斷
    let result = null;
    try {
        result = await response.json();
    } catch {
        result = null;
    }

    if (!response.ok) {
        const detail = result ? result.detail : null;
        let message = "發生錯誤，請稍後再試";

        if (typeof detail === "string") {
            message = detail;
        } else if (Array.isArray(detail)) {
            // FastAPI 欄位格式錯誤（422）時 detail 是陣列
            message = "資料格式有誤，請檢查是否有欄位未填";
        } else if (detail && detail.message) {
            message = detail.message;
        }

        const error = new Error(message);
        error.status = response.status;
        error.detail = detail;
        throw error;
    }

    return result;
}


// ----------------------------------------------------------
// 取得目前登入者
// 已登入：回傳 { id, name, role }
// 未登入：回傳 null（不會跳頁，給公開頁面使用）
// ----------------------------------------------------------
async function getCurrentUser() {
    try {
        return await api("/api/auth/me");
    } catch {
        return null;
    }
}


// ----------------------------------------------------------
// 需要登入的頁面在一開始呼叫
// roles：允許的角色陣列，例如 ["admin"]；不傳表示只要登入就可以
// 未登入：跳到登入頁，登入後會自動回到這一頁
// 角色不符：跳回首頁
// 通過：回傳目前登入者
// ----------------------------------------------------------
async function requireLogin(roles = null) {
    const user = await getCurrentUser();

    if (user === null) {
        const next = encodeURIComponent(location.pathname + location.search);
        location.href = "/common/login.html?next=" + next;
        return new Promise(() => {});   // 停在這裡，不繼續執行後面的程式
    }

    if (roles && !roles.includes(user.role)) {
        alert("沒有權限使用此頁面");
        location.href = "/";
        return new Promise(() => {});
    }

    return user;
}


// ----------------------------------------------------------
// 跳到登入頁（例如未登入時按下「申請借用」）
// 登入後會自動回到目前這一頁
// ----------------------------------------------------------
function goToLogin() {
    const next = encodeURIComponent(location.pathname + location.search);
    location.href = "/common/login.html?next=" + next;
}


// ----------------------------------------------------------
// 產生導覽列，放在 <body> 最上方
// 會回傳目前登入者（未登入時是 null），頁面可以直接拿來用
//   const user = await renderNavbar();
// ----------------------------------------------------------
async function renderNavbar() {
    const user = await getCurrentUser();

    let config = { allow_self_register: true };
    if (user === null) {
        try {
            config = await api("/api/auth/config");
        } catch {
            // 取不到設定時維持預設值
        }
    }

    // 模組連結：目前所在的模組加上 active
    let linksHtml = "";
    for (const link of NAV_LINKS) {
        const active = location.pathname.startsWith(link.href) ? "active" : "";
        linksHtml += `<a href="${link.href}" class="${active}">${link.text}</a>`;
    }
    if (user && user.role === "admin") {
        const active = location.pathname.startsWith("/common/admin_users") ? "active" : "";
        linksHtml += `<a href="/common/admin_users.html" class="${active}">帳號管理</a>`;
    }

    // 右側：登入者資訊
    let userHtml = "";
    if (user) {
        userHtml = `
            <span>${escapeHtml(user.name)}（${ROLE_NAMES[user.role]}）</span>
            <button class="btn btn-outline-white" id="navbar-logout">登出</button>
        `;
    } else {
        userHtml = `<a class="btn btn-outline-white" href="/common/login.html">登入</a>`;
        if (config.allow_self_register) {
            userHtml += `<a class="btn btn-outline-white" href="/common/register.html">註冊</a>`;
        }
    }

    const navbar = document.createElement("nav");
    navbar.className = "navbar";
    navbar.innerHTML = `
        <a class="navbar-brand" href="/">管院空間管理系統</a>
        <div class="navbar-links">${linksHtml}</div>
        <div class="navbar-user">${userHtml}</div>
    `;
    document.body.prepend(navbar);

    const logoutButton = document.getElementById("navbar-logout");
    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            await api("/api/auth/logout", { method: "POST" });
            location.href = "/";
        });
    }

    return user;
}


// ----------------------------------------------------------
// 在指定的元素顯示訊息
// type："error"（紅）、"success"（綠）、"info"（黃）
// text 傳空字串時清除訊息
// ----------------------------------------------------------
function showMessage(element, text, type = "error") {
    element.className = "message message-" + type;
    element.textContent = text;
}
