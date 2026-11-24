// ==========================================================
// www/index.js：首頁（公開，不需要登入）
// ==========================================================

async function init() {
    const user = await renderNavbar();

    if (user) {
        document.getElementById("welcome-text").textContent =
            `${user.name}（${ROLE_NAMES[user.role]}）您好，請選擇要使用的功能。`;
    }
}

init();
