// ==========================================================
// www/common/login.js：登入頁
//   - 登入成功：回到 ?next= 指定的頁面，沒有的話回首頁
//   - 審核中：顯示提醒
//   - 被退件：顯示退件原因與重新申請表單
// ==========================================================

const loginSection = document.getElementById("login-section");
const reapplySection = document.getElementById("reapply-section");
const loginMessage = document.getElementById("login-message");
const reapplyMessage = document.getElementById("reapply-message");


// ----------------------------------------------------------
// 取得登入後要回去的頁面
// 只接受站內路徑（以 / 開頭、不是 //），避免被導到其他網站
// ----------------------------------------------------------
function getNextPage() {
    const next = new URLSearchParams(location.search).get("next");
    if (next && next.startsWith("/") && !next.startsWith("//")) {
        return next;
    }
    return "/";
}


// ----------------------------------------------------------
// 登入
// ----------------------------------------------------------
document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();   // 阻止表單預設的重新整理頁面
    showMessage(loginMessage, "");

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
        await api("/api/auth/login", {
            method: "POST",
            data: { username, password },
        });
        location.href = getNextPage();
    } catch (error) {
        const detail = error.detail;

        if (detail && detail.status === "pending") {
            showMessage(loginMessage, error.message, "info");
        } else if (detail && detail.status === "rejected") {
            showReapplyForm(username, detail);
        } else {
            showMessage(loginMessage, error.message, "error");
        }
    }
});


// ----------------------------------------------------------
// 顯示重新申請表單，預先填入原本申請的姓名與身分
// ----------------------------------------------------------
function showReapplyForm(username, detail) {
    loginSection.classList.add("hidden");
    reapplySection.classList.remove("hidden");

    document.getElementById("reject-comment").textContent = detail.comment;
    document.getElementById("reapply-username").value = username;
    document.getElementById("reapply-name").value = detail.name;
    document.getElementById("reapply-role").value = detail.role;
}


// ----------------------------------------------------------
// 重新申請
// ----------------------------------------------------------
document.getElementById("reapply-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(reapplyMessage, "");

    try {
        const result = await api("/api/auth/reapply", {
            method: "POST",
            data: {
                username: document.getElementById("reapply-username").value,
                password: document.getElementById("reapply-password").value,
                name: document.getElementById("reapply-name").value,
                role: document.getElementById("reapply-role").value,
            },
        });
        showMessage(reapplyMessage, result.message, "success");
        document.querySelector("#reapply-form button").disabled = true;
    } catch (error) {
        showMessage(reapplyMessage, error.message, "error");
    }
});


// ----------------------------------------------------------
// 頁面載入：已登入就直接離開；關閉自行註冊時隱藏申請連結
// ----------------------------------------------------------
async function init() {
    const user = await renderNavbar();
    if (user) {
        location.href = getNextPage();
        return;
    }

    try {
        const config = await api("/api/auth/config");
        if (!config.allow_self_register) {
            document.getElementById("register-link").classList.add("hidden");
        }
    } catch {
        // 取不到設定時維持顯示
    }
}

init();
