// Alerts & Notifications JavaScript
const API = '';
let allAlerts = [];
let allNotifications = [];
let alertMap = null;
let alertMarker = null;
let alertCircle = null;

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    if (tab === 'alerts') {
        event.target.classList.add('active');
        document.getElementById('alertsSection').classList.remove('hidden');
        document.getElementById('notificationsSection').classList.add('hidden');
    } else {
        event.target.classList.add('active');
        document.getElementById('alertsSection').classList.add('hidden');
        document.getElementById('notificationsSection').classList.remove('hidden');
    }
}

// ===== Alerts =====
async function loadAlerts() {
    try {
        const res = await fetch(`${API}/api/admin/alerts`);
        allAlerts = await res.json();
        renderAlerts(allAlerts);
    } catch (e) { console.error('Failed to load alerts:', e); }
}

function renderAlerts(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    tbody.innerHTML = alerts.map(a => `
        <tr>
            <td><strong>${a.name}</strong></td>
            <td><span class="alert-type-${a.alert_type}">${getAlertTypeEmoji(a.alert_type)} ${a.alert_type}</span></td>
            <td><span class="badge badge-${getSeverityBadge(a.severity)}">${a.severity}</span></td>
            <td>${a.latitude.toFixed(4)}, ${a.longitude.toFixed(4)}</td>
            <td>${a.radius_km} km</td>
            <td>${formatDate(a.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="editAlert(${a.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAlert(${a.id})" style="margin-left:4px;">🗑️</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="7">No alerts</td></tr>';
}

function filterAlerts() {
    const q = document.getElementById('alertSearch').value.toLowerCase();
    renderAlerts(allAlerts.filter(a => a.name.toLowerCase().includes(q) || a.alert_type.toLowerCase().includes(q)));
}

function getAlertTypeEmoji(type) {
    const map = { rain: '🌧️', landslide: '🏔️', weather: '🌪️', emergency: '🆘', flood: '🌊', other: '⚡' };
    return map[type] || '⚡';
}

function getSeverityBadge(severity) {
    const map = { info: 'info', warning: 'warning', danger: 'danger', critical: 'danger' };
    return map[severity] || 'info';
}

// India bounds for map and place search
const INDIA_CENTER = [20.5937, 78.9629];
const INDIA_ZOOM = 5;
const INDIA_VIEWBOX = '8.0,68.0,35.0,97.0'; // south,west,north,east

async function searchAlertPlace() {
    const q = document.getElementById('alertPlaceSearch').value.trim();
    const resultsEl = document.getElementById('alertPlaceResults');
    if (!q) { resultsEl.style.display = 'none'; return; }
    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&countrycodes=in&viewbox=${INDIA_VIEWBOX}&bounded=1&limit=8`;
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        const list = await res.json();
        if (!list.length) {
            resultsEl.innerHTML = '<div style="padding:8px;color:#64748b;">No places found in India. Try another name.</div>';
        } else {
            resultsEl.innerHTML = list.map(p => `
                <div class="alert-place-result" data-lat="${p.lat}" data-lng="${p.lon}" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid #e2e8f0;font-size:13px;">
                    <strong>${p.display_name.split(',').slice(0, 2).join(', ')}</strong>
                </div>
            `).join('');
            resultsEl.querySelectorAll('.alert-place-result').forEach(el => {
                el.addEventListener('click', function () {
                    const lat = parseFloat(this.dataset.lat);
                    const lng = parseFloat(this.dataset.lng);
                    document.getElementById('alertLat').value = lat.toFixed(6);
                    document.getElementById('alertLng').value = lng.toFixed(6);
                    if (alertMap) {
                        alertMap.setView([lat, lng], 12);
                        updateAlertMapMarker(lat, lng);
                    }
                    resultsEl.style.display = 'none';
                });
            });
        }
        resultsEl.style.display = 'block';
    } catch (e) {
        resultsEl.innerHTML = '<div style="padding:8px;color:#ef4444;">Search failed. Try again.</div>';
        resultsEl.style.display = 'block';
    }
}

function showAlertForm(alert = null) {
    document.getElementById('alertFormTitle').textContent = alert ? 'Edit Alert' : 'Send Alert';
    document.getElementById('editAlertId').value = alert ? alert.id : '';
    document.getElementById('alertName').value = alert ? alert.name : '';
    document.getElementById('alertType').value = alert ? alert.alert_type : 'rain';
    document.getElementById('alertSeverity').value = alert ? alert.severity : 'warning';
    document.getElementById('alertDescription').value = alert ? alert.description || '' : '';
    document.getElementById('alertLat').value = alert ? alert.latitude : '';
    document.getElementById('alertLng').value = alert ? alert.longitude : '';
    document.getElementById('alertRadius').value = alert ? alert.radius_km : 10;
    document.getElementById('alertPlaceSearch').value = '';
    document.getElementById('alertPlaceResults').style.display = 'none';
    document.getElementById('alertFormModal').classList.remove('hidden');

    setTimeout(() => {
        if (!alertMap) {
            alertMap = L.map('alertMap').setView(INDIA_CENTER, INDIA_ZOOM);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(alertMap);
            alertMap.on('click', function (e) {
                document.getElementById('alertLat').value = e.latlng.lat.toFixed(6);
                document.getElementById('alertLng').value = e.latlng.lng.toFixed(6);
                updateAlertMapMarker(e.latlng.lat, e.latlng.lng);
            });
        }
        alertMap.invalidateSize();
        if (alert) {
            alertMap.setView([alert.latitude, alert.longitude], 12);
            updateAlertMapMarker(alert.latitude, alert.longitude);
        } else {
            alertMap.setView(INDIA_CENTER, INDIA_ZOOM);
        }
    }, 200);
}

function updateAlertMapMarker(lat, lng) {
    if (alertMarker) alertMap.removeLayer(alertMarker);
    if (alertCircle) alertMap.removeLayer(alertCircle);
    alertMarker = L.marker([lat, lng]).addTo(alertMap);
    const radius = parseFloat(document.getElementById('alertRadius').value) || 10;
    alertCircle = L.circle([lat, lng], { radius: radius * 1000, color: '#ef4444', fillOpacity: 0.15 }).addTo(alertMap);
}

function editAlert(alertId) {
    const alert = allAlerts.find(a => a.id === alertId);
    if (alert) showAlertForm(alert);
}

async function saveAlert() {
    const editId = document.getElementById('editAlertId').value;
    const body = {
        name: document.getElementById('alertName').value,
        alert_type: document.getElementById('alertType').value,
        severity: document.getElementById('alertSeverity').value,
        description: document.getElementById('alertDescription').value,
        latitude: parseFloat(document.getElementById('alertLat').value),
        longitude: parseFloat(document.getElementById('alertLng').value),
        radius_km: parseFloat(document.getElementById('alertRadius').value)
    };

    if (!body.name || isNaN(body.latitude) || isNaN(body.longitude)) {
        alert('Please fill in required fields and select location on map');
        return;
    }

    try {
        const url = editId ? `${API}/api/admin/alerts/${editId}` : `${API}/api/admin/alerts`;
        const res = await fetch(url, {
            method: editId ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const contentType = res.headers.get('Content-Type') || '';
        let data;
        if (contentType.includes('application/json')) {
            data = await res.json();
        } else {
            const text = await res.text();
            alert('Server error: ' + (res.status === 500 ? 'Internal error' : res.status) + '. ' + (text.slice(0, 80) || 'Invalid response'));
            return;
        }
        if (!res.ok) {
          const msg = [data.error, data.detail].filter(Boolean).join(' — ') || 'Failed';
          alert(msg);
          return;
        }
        if (!editId && data.affected_users > 0) {
            alert(`Alert sent! ${data.affected_users} users in the affected area.`);
        }
        closeModal('alertFormModal');
        loadAlerts();
    } catch (e) { alert('Error: ' + e.message); }
}

async function deleteAlert(id) {
    if (!confirm('Delete this alert?')) return;
    await fetch(`${API}/api/admin/alerts/${id}`, { method: 'DELETE' });
    loadAlerts();
}

// ===== Notifications =====
async function loadNotifications() {
    try {
        const res = await fetch(`${API}/api/admin/notifications`);
        allNotifications = await res.json();
        renderNotifications(allNotifications);
    } catch (e) { console.error('Failed to load notifications:', e); }
}

function renderNotifications(notifs) {
    const tbody = document.getElementById('notificationsTableBody');
    tbody.innerHTML = notifs.map(n => `
        <tr>
            <td><strong>${n.name}</strong></td>
            <td>${n.description.substring(0, 60)}${n.description.length > 60 ? '...' : ''}</td>
            <td>${n.start_date}</td>
            <td>${n.end_date}</td>
            <td><span class="badge ${n.is_done ? 'badge-success' : n.is_active ? 'badge-info' : 'badge-warning'}">${n.is_done ? 'Done' : n.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                ${!n.is_done ? `<button class="btn btn-sm btn-success" onclick="markDone(${n.id})">✓ Done</button>` : ''}
                <button class="btn btn-sm btn-outline" onclick="editNotification(${n.id})" style="margin-left:4px;">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteNotification(${n.id})" style="margin-left:4px;">🗑️</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="6">No notifications</td></tr>';
}

function showNotificationForm(notif = null) {
    document.getElementById('notifFormTitle').textContent = notif ? 'Edit Notification' : 'Send Notification';
    document.getElementById('editNotifId').value = notif ? notif.id : '';
    document.getElementById('notifName').value = notif ? notif.name : '';
    document.getElementById('notifDescription').value = notif ? notif.description : '';
    document.getElementById('notifStartDate').value = notif ? notif.start_date : new Date().toISOString().split('T')[0];
    document.getElementById('notifEndDate').value = notif ? notif.end_date : '';
    document.getElementById('notifFormModal').classList.remove('hidden');
}

function editNotification(id) {
    const n = allNotifications.find(x => x.id === id);
    if (n) showNotificationForm(n);
}

async function saveNotification() {
    const editId = document.getElementById('editNotifId').value;
    const body = {
        name: document.getElementById('notifName').value,
        description: document.getElementById('notifDescription').value,
        start_date: document.getElementById('notifStartDate').value,
        end_date: document.getElementById('notifEndDate').value
    };
    if (!body.name || !body.description || !body.start_date || !body.end_date) {
        alert('Please fill all required fields'); return;
    }
    try {
        const url = editId ? `${API}/api/admin/notifications/${editId}` : `${API}/api/admin/notifications`;
        await fetch(url, { method: editId ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        closeModal('notifFormModal');
        loadNotifications();
    } catch (e) { alert('Error: ' + e.message); }
}

async function markDone(id) {
    await fetch(`${API}/api/admin/notifications/${id}/done`, { method: 'POST' });
    loadNotifications();
}

async function deleteNotification(id) {
    if (!confirm('Delete this notification?')) return;
    await fetch(`${API}/api/admin/notifications/${id}`, { method: 'DELETE' });
    loadNotifications();
}

function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
function formatDate(d) { if (!d) return '—'; return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }

loadAlerts();
loadNotifications();
