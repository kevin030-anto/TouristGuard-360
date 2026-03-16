// Dashboard JavaScript
const API = '';
let allUsers = [];

async function loadStats() {
    try {
        const res = await fetch(`${API}/api/admin/dashboard-stats`);
        const data = await res.json();
        document.getElementById('totalUsers').textContent = data.total_users;
        document.getElementById('activeUsers').textContent = data.active_users;
        document.getElementById('activeAlerts').textContent = data.active_alerts;
        document.getElementById('dangerZones').textContent = data.danger_zones;
        document.getElementById('activeSOS').textContent = data.active_sos;
        if (document.getElementById('resolvedSOS')) {
            document.getElementById('resolvedSOS').textContent = data.resolved_sos;
        }
        document.getElementById('totalDocs').textContent = data.total_documents;
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API}/api/admin/users`);
        allUsers = await res.json();
        renderUsers(allUsers);
    } catch (e) {
        console.error('Failed to load users:', e);
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = users.map(u => `
        <tr onclick="showUserDetail(${u.id})">
            <td><strong>${u.full_name || 'N/A'}</strong></td>
            <td>${u.email}</td>
            <td>${u.country || '—'}</td>
            <td>${u.blood_group || '—'}</td>
            <td>${formatDate(u.created_at)}</td>
            <td>${formatDate(u.last_login)}</td>
            <td><span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); editUser(${u.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteUser(${u.id})" style="margin-left:4px;">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function filterUsers() {
    const q = document.getElementById('userSearch').value.toLowerCase();
    const filtered = allUsers.filter(u =>
        (u.full_name || '').toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.country || '').toLowerCase().includes(q)
    );
    renderUsers(filtered);
}

async function showUserDetail(userId) {
    try {
        const res = await fetch(`${API}/api/admin/users/${userId}`);
        const u = await res.json();
        document.getElementById('userDetailTitle').textContent = u.full_name || 'User Details';
        document.getElementById('userDetailBody').innerHTML = `
            <div class="user-detail">
                <div class="detail-item"><label>Email</label><div class="value">${u.email}</div></div>
                <div class="detail-item"><label>Full Name</label><div class="value">${u.full_name || '—'}</div></div>
                <div class="detail-item"><label>Age</label><div class="value">${u.age || '—'}</div></div>
                <div class="detail-item"><label>Country</label><div class="value">${u.country || '—'}</div></div>
                <div class="detail-item"><label>Blood Group</label><div class="value">${u.blood_group || '—'}</div></div>
                <div class="detail-item"><label>Phone</label><div class="value">${u.phone_country_code || ''} ${u.phone || '—'}</div></div>
                <div class="detail-item"><label>Emergency Contact 1</label><div class="value">${u.emergency_contact_1_code || ''} ${u.emergency_contact_1 || '—'}</div></div>
                <div class="detail-item"><label>Emergency Contact 2</label><div class="value">${u.emergency_contact_2_code || ''} ${u.emergency_contact_2 || '—'}</div></div>
                <div class="detail-item"><label>Emergency Contact 3</label><div class="value">${u.emergency_contact_3_code || ''} ${u.emergency_contact_3 || '—'}</div></div>
                <div class="detail-item"><label>Auth Provider</label><div class="value">${u.auth_provider}</div></div>
                <div class="detail-item"><label>Documents</label><div class="value">${u.document_count} files</div></div>
                <div class="detail-item"><label>Location</label><div class="value">${u.last_known_lat ? `${u.last_known_lat.toFixed(4)}, ${u.last_known_lng.toFixed(4)}` : 'Unknown'}</div></div>
                <div class="detail-item"><label>Registered</label><div class="value">${formatDate(u.created_at)}</div></div>
                <div class="detail-item"><label>Last Login</label><div class="value">${formatDate(u.last_login)}</div></div>
            </div>
            <h4 style="margin-top: 24px; margin-bottom: 12px;">📋 Activity Log (Recent 10)</h4>
            <table>
                <thead><tr><th>Action</th><th>Details</th><th>Time</th></tr></thead>
                <tbody>
                    ${(u.activity_log || []).slice(0, 10).map(a => `
                        <tr><td>${a.action}</td><td>${a.details || '—'}</td><td>${formatDate(a.created_at)}</td></tr>
                    `).join('') || '<tr><td colspan="3">No activity logs</td></tr>'}
                </tbody>
            </table>
            <h4 style="margin-top: 24px; margin-bottom: 12px;">🆘 Emergency History</h4>
            <table>
                <thead><tr><th>ID</th><th>Location</th><th>Status</th><th>Time</th></tr></thead>
                <tbody>
                    ${(u.emergency_history || []).map(e => `
                        <tr><td>#${e.id}</td><td>${e.lat.toFixed(4)}, ${e.lng.toFixed(4)}</td><td><span class="badge ${e.status === 'active' ? 'badge-danger' : 'badge-success'}">${e.status}</span></td><td>${formatDate(e.created_at)}</td></tr>
                    `).join('') || '<tr><td colspan="4">No emergencies</td></tr>'}
                </tbody>
            </table>
        `;
        document.getElementById('userDetailModal').classList.remove('hidden');
    } catch (e) {
        console.error('Failed to load user detail:', e);
    }
}

function showAddUserModal() {
    document.getElementById('userFormTitle').textContent = 'Add User';
    document.getElementById('editUserId').value = '';
    document.getElementById('userForm').reset();
    document.getElementById('formPassword').required = true;
    document.getElementById('userFormModal').classList.remove('hidden');
}

function editUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    document.getElementById('userFormTitle').textContent = 'Edit User';
    document.getElementById('editUserId').value = userId;
    document.getElementById('formName').value = user.full_name || '';
    document.getElementById('formEmail').value = user.email;
    document.getElementById('formAge').value = user.age || '';
    document.getElementById('formCountry').value = user.country || '';
    document.getElementById('formBloodGroup').value = user.blood_group || '';
    document.getElementById('formPhone').value = user.phone || '';
    document.getElementById('formPassword').required = false;
    document.getElementById('formPassword').value = '';
    document.getElementById('userFormModal').classList.remove('hidden');
}

async function saveUser() {
    const editId = document.getElementById('editUserId').value;
    const body = {
        full_name: document.getElementById('formName').value,
        email: document.getElementById('formEmail').value,
        age: parseInt(document.getElementById('formAge').value) || null,
        country: document.getElementById('formCountry').value || null,
        blood_group: document.getElementById('formBloodGroup').value || null,
        phone: document.getElementById('formPhone').value || null,
    };
    const pwd = document.getElementById('formPassword').value;
    if (pwd) body.password = pwd;

    try {
        const url = editId ? `${API}/api/admin/users/${editId}` : `${API}/api/admin/users`;
        const method = editId ? 'PUT' : 'POST';
        if (!editId && !pwd) { alert('Password is required for new users'); return; }

        const res = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (!res.ok) { alert(data.error || 'Failed to save'); return; }
        closeModal('userFormModal');
        loadUsers();
        loadStats();
    } catch (e) {
        alert('Error saving user: ' + e.message);
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    try {
        await fetch(`${API}/api/admin/users/${userId}`, { method: 'DELETE' });
        loadUsers();
        loadStats();
    } catch (e) {
        alert('Error deleting user: ' + e.message);
    }
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Init
let autoRefreshInterval = null;
let isAutoRefresh = true;

function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        loadStats();
        loadUsers();
        updateLastRefreshed();
    }, 500); // Refresh every 0.5 seconds
}

function updateLastRefreshed() {
    const el = document.getElementById('lastRefreshed');
    if (el) {
        el.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    }
}

function toggleDashboardAutoRefresh() {
    isAutoRefresh = !isAutoRefresh;
    const btn = document.getElementById('dashAutoRefreshBtn');
    if (isAutoRefresh) {
        startAutoRefresh();
        if (btn) btn.innerHTML = '⏸️ Auto-Refresh: ON (0.5s)';
    } else {
        clearInterval(autoRefreshInterval);
        if (btn) btn.innerHTML = '▶ Auto-Refresh: OFF';
    }
}

// Add auto-refresh indicator to page header
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.page-header');
    if (header) {
        const indicator = document.createElement('div');
        indicator.style.cssText = 'display:flex;align-items:center;gap:12px;margin-top:8px;';
        indicator.innerHTML = `
            <span id="lastRefreshed" style="font-size:12px;color:#94a3b8;">Last updated: ${new Date().toLocaleTimeString()}</span>
            <button class="btn btn-sm btn-success" id="dashAutoRefreshBtn" onclick="toggleDashboardAutoRefresh()">⏸️ Auto-Refresh: ON (0.5s)</button>
        `;
        header.appendChild(indicator);
    }
});

loadStats();
loadUsers();
startAutoRefresh();

