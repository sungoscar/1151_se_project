// ==========================================================
// www/common/admin_users.js：帳號管理頁（限管理員）
//   分頁 1 待審核：核准（可更正身分）、退件（必填原因）
//   分頁 2 全部帳號：可依狀態篩選
//   分頁 3 新增帳號：管理員直接建立，建立後即可登入
// ==========================================================

const pageMessage = document.getElementById("page-message");


// ----------------------------------------------------------
// 分頁切換
// ----------------------------------------------------------
for (const tab of document.querySelectorAll(".tab")) {
    tab.addEventListener("click", () => {
        for (const other of document.querySelectorAll(".tab")) {
            other.classList.toggle("active", other === tab);
        }
        for (const panel of document.querySelectorAll(".tab-panel")) {
            panel.classList.toggle("hidden", panel.id !== "panel-" + tab.dataset.tab);
        }
        showMessage(pageMessage, "");

        if (tab.dataset.tab === "pending") loadPendingUsers();
        if (tab.dataset.tab === "all") loadAllUsers();
    });
}


// ----------------------------------------------------------
// 分頁 1：待審核清單
// 身分欄是下拉選單，預設為申請人自己選的身分，管理員可以更正後再核准
// ----------------------------------------------------------
async function loadPendingUsers() {
    const tbody = document.getElementById("pending-list");

    try {
        const users = await api("/api/auth/users?status=pending");
        document.getElementById("pending-count").textContent = users.length > 0 ? users.length : "";

        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="table-empty">目前沒有待審核的帳號</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        for (const user of users) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.name)}</td>
                <td>
                    <select class="input-small role-select">
                        <option value="student" ${user.role === "student" ? "selected" : ""}>學生</option>
                        <option value="teacher" ${user.role === "teacher" ? "selected" : ""}>老師</option>
                    </select>
                </td>
                <td>${escapeHtml(user.created_at)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-small approve-button">核准</button>
                        <button class="btn btn-small btn-danger reject-button">退件</button>
                    </div>
                </td>
            `;

            row.querySelector(".approve-button").addEventListener("click", () => {
                approveUser(user, row.querySelector(".role-select").value);
            });
            row.querySelector(".reject-button").addEventListener("click", () => {
                toggleRejectRow(row, user);
            });

            tbody.appendChild(row);
        }
    } catch (error) {
        showMessage(pageMessage, error.message, "error");
    }
}


// ----------------------------------------------------------
// 核准
// ----------------------------------------------------------
async function approveUser(user, role) {
    try {
        await api(`/api/auth/users/${user.id}/approve`, {
            method: "POST",
            data: { role },
        });
        showMessage(pageMessage, `已核准 ${user.name}（${ROLE_NAMES[role]}）`, "success");
        loadPendingUsers();
    } catch (error) {
        showMessage(pageMessage, error.message, "error");
    }
}


// ----------------------------------------------------------
// 退件：在該列下方展開原因輸入框，再按一次「退件」則收合
// ----------------------------------------------------------
function toggleRejectRow(row, user) {
    const next = row.nextElementSibling;
    if (next && next.classList.contains("reject-row")) {
        next.remove();
        return;
    }

    const rejectRow = document.createElement("tr");
    rejectRow.className = "reject-row";
    rejectRow.innerHTML = `
        <td colspan="5">
            <div class="reject-box">
                <label>退件原因</label>
                <input type="text" class="input-small" placeholder="例如：身分不符，請確認">
                <button class="btn btn-small btn-danger">確認退件</button>
            </div>
        </td>
    `;
    row.after(rejectRow);

    const input = rejectRow.querySelector("input");
    input.focus();

    rejectRow.querySelector("button").addEventListener("click", async () => {
        try {
            await api(`/api/auth/users/${user.id}/reject`, {
                method: "POST",
                data: { comment: input.value },
            });
            showMessage(pageMessage, `已退件 ${user.name}`, "success");
            loadPendingUsers();
        } catch (error) {
            showMessage(pageMessage, error.message, "error");
        }
    });
}


// ----------------------------------------------------------
// 分頁 2：全部帳號
// ----------------------------------------------------------
async function loadAllUsers() {
    const tbody = document.getElementById("all-list");
    const status = document.getElementById("status-filter").value;

    try {
        const users = await api("/api/auth/users?status=" + encodeURIComponent(status));

        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="table-empty">沒有符合的帳號</td></tr>`;
            return;
        }

        tbody.innerHTML = users.map((user) => `
            <tr>
                <td>${escapeHtml(user.username)}</td>
                <td>${escapeHtml(user.name)}</td>
                <td>${ROLE_NAMES[user.role]}</td>
                <td><span class="tag tag-${user.status}">${STATUS_NAMES[user.status]}</span></td>
                <td>${escapeHtml(user.review_comment)}</td>
                <td>${escapeHtml(user.created_at)}</td>
                <td>${escapeHtml(user.reviewed_at)}</td>
            </tr>
        `).join("");
    } catch (error) {
        showMessage(pageMessage, error.message, "error");
    }
}

document.getElementById("status-filter").addEventListener("change", loadAllUsers);


// ----------------------------------------------------------
// 分頁 3：新增帳號
// ----------------------------------------------------------
const createForm = document.getElementById("create-form");
const createMessage = document.getElementById("create-message");

createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(createMessage, "");

    try {
        const result = await api("/api/auth/users", {
            method: "POST",
            data: {
                username: document.getElementById("create-username").value.trim(),
                password: document.getElementById("create-password").value,
                name: document.getElementById("create-name").value,
                role: document.getElementById("create-role").value,
            },
        });
        showMessage(createMessage, result.message, "success");
        createForm.reset();
    } catch (error) {
        showMessage(createMessage, error.message, "error");
    }
});


// ----------------------------------------------------------
// 頁面載入：限管理員
// ----------------------------------------------------------
async function init() {
    await requireLogin(["admin"]);
    await renderNavbar();
    loadPendingUsers();
}

init();
