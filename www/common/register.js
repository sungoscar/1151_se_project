// ==========================================================
// www/common/register.js：申請帳號頁
// 送出後狀態為「待審核」，管理員核准後才能登入
// ==========================================================

const registerForm = document.getElementById("register-form");
const registerMessage = document.getElementById("register-message");


registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(registerMessage, "");

    const password = document.getElementById("password").value;
    const passwordConfirm = document.getElementById("password-confirm").value;

    // 兩次密碼不同時，不用送到後端就可以先提醒
    if (password !== passwordConfirm) {
        showMessage(registerMessage, "兩次輸入的密碼不一致", "error");
        return;
    }

    try {
        const result = await api("/api/auth/register", {
            method: "POST",
            data: {
                username: document.getElementById("username").value.trim(),
                password: password,
                name: document.getElementById("name").value,
                role: document.getElementById("role").value,
            },
        });
        showMessage(registerMessage, result.message, "success");
        registerForm.classList.add("hidden");
    } catch (error) {
        showMessage(registerMessage, error.message, "error");
    }
});


// ----------------------------------------------------------
// 頁面載入：已登入就回首頁；關閉自行註冊時隱藏表單
// ----------------------------------------------------------
async function init() {
    const user = await renderNavbar();
    if (user) {
        location.href = "/";
        return;
    }

    const config = await api("/api/auth/config");
    if (!config.allow_self_register) {
        registerForm.classList.add("hidden");
        showMessage(registerMessage, "目前不開放自行註冊，請洽管理員建立帳號", "info");
    }
}

init();
