// SOS Monitor JavaScript
const API = '';
let sosMap = null;
let sosMarkers = [];
let allSOSHistory = [];
let sosAutoRefreshInterval = null;
let sosAutoRefreshOn = true;

// Initialize map
function initSOSMap() {
    sosMap = L.map('sosMap').setView([20.5937, 78.9629], 5); // India center
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(sosMap);
}

// Load all SOS data
async function loadSOSData() {
    await Promise.all([loadActiveEmergencies(), loadSOSHistory(), loadSOSStats()]);
    updateSOSTimestamp();
}

// Load active emergencies
async function loadActiveEmergencies() {
    try {
        const res = await fetch(`${API}/api/emergency/active`);
        const data = await res.json();
        renderActiveSOSList(data);
        updateSOSMapMarkers(data);
        document.getElementById('sosActiveCount').textContent = data.length;
    } catch (e) {
        console.error('Failed to load active emergencies:', e);
    }
}

// Load SOS history
async function loadSOSHistory() {
    try {
        const res = await fetch(`${API}/api/admin/sos-history`);
        allSOSHistory = await res.json();
        renderSOSHistory(allSOSHistory);

        // Calculate stats
        const total = allSOSHistory.length;
        const resolvedToday = allSOSHistory.filter(s => {
            if (s.status !== 'resolved' || !s.resolved_at) return false;
            const today = new Date().toDateString();
            return new Date(s.resolved_at).toDateString() === today;
        }).length;

        document.getElementById('sosTotalCount').textContent = total;
        document.getElementById('sosResolvedCount').textContent = resolvedToday;
    } catch (e) {
        console.error('Failed to load SOS history:', e);
    }
}

// Load SOS Stats
async function loadSOSStats() {
    try {
        const res = await fetch(`${API}/api/admin/dashboard-stats`);
        const data = await res.json();
        document.getElementById('sosActiveCount').textContent = data.active_sos;
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

// Render active SOS alerts
function renderActiveSOSList(emergencies) {
    const container = document.getElementById('activeSOSList');
    if (emergencies.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding: 40px; color: #94a3b8;">
                <div style="font-size: 48px; margin-bottom: 12px;">✅</div>
                <h3 style="color: #22c55e;">No Active SOS Alerts</h3>
                <p>All emergencies have been resolved</p>
            </div>`;
        return;
    }

    container.innerHTML = emergencies.map(e => `
        <div class="card" style="margin-bottom: 12px; border-left: 4px solid var(--danger); padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h4 style="margin: 0; color: var(--danger);">🆘 SOS #${e.id} — ${e.user_name || 'Unknown User'}</h4>
                    <div style="margin-top: 8px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 14px;">
                        <span>📧 ${e.user_email || '—'}</span>
                        <span>📞 ${e.user_phone || '—'}</span>
                        <span>🩸 Blood: ${e.blood_group || '—'}</span>
                        <span>📍 ${e.latitude?.toFixed(4)}, ${e.longitude?.toFixed(4)}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 12px; color: #94a3b8;">
                        Triggered: ${formatSOSDate(e.created_at)}
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-sm btn-outline" onclick="focusOnSOS(${e.latitude}, ${e.longitude})">📍 Locate</button>
                    <button class="btn btn-sm btn-success" onclick="resolveSOS(${e.id})">✅ Resolve</button>
                </div>
            </div>
        </div>
    `).join('');
}

// Update map markers for active SOS
function updateSOSMapMarkers(emergencies) {
    // Clear existing markers
    sosMarkers.forEach(m => sosMap.removeLayer(m));
    sosMarkers = [];

    if (emergencies.length === 0) return;

    const bounds = [];

    emergencies.forEach(e => {
        if (!e.latitude || !e.longitude) return;

        const icon = L.divIcon({
            html: `<div style="
                background: #ef4444;
                color: white;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                border: 3px solid white;
                box-shadow: 0 2px 10px rgba(239,68,68,0.5);
                animation: pulse-marker 1.5s ease-in-out infinite;
            ">🆘</div>`,
            className: 'sos-marker',
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });

        const marker = L.marker([e.latitude, e.longitude], { icon })
            .addTo(sosMap)
            .bindPopup(`
                <div style="min-width: 200px;">
                    <h3 style="margin:0; color:#ef4444;">🆘 SOS #${e.id}</h3>
                    <hr style="margin: 8px 0;">
                    <p><strong>👤</strong> ${e.user_name || 'Unknown'}</p>
                    <p><strong>📧</strong> ${e.user_email || '—'}</p>
                    <p><strong>📞</strong> ${e.user_phone || '—'}</p>
                    <p><strong>🩸</strong> ${e.blood_group || '—'}</p>
                    <p><strong>📍</strong> ${e.latitude?.toFixed(4)}, ${e.longitude?.toFixed(4)}</p>
                    <p><strong>⏰</strong> ${formatSOSDate(e.created_at)}</p>
                    <button onclick="resolveSOS(${e.id})" style="
                        width: 100%; padding: 8px; margin-top: 8px;
                        background: #22c55e; color: white; border: none;
                        border-radius: 6px; cursor: pointer; font-weight: bold;
                    ">✅ Resolve Emergency</button>
                </div>
            `);

        sosMarkers.push(marker);
        bounds.push([e.latitude, e.longitude]);
    });

    if (bounds.length > 0) {
        sosMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
}

// Focus map on a specific SOS
function focusOnSOS(lat, lng) {
    sosMap.setView([lat, lng], 15);
    sosMarkers.forEach(m => {
        if (Math.abs(m.getLatLng().lat - lat) < 0.001 && Math.abs(m.getLatLng().lng - lng) < 0.001) {
            m.openPopup();
        }
    });
}

// Resolve an SOS
async function resolveSOS(sosId) {
    if (!confirm('Are you sure you want to resolve this SOS alert?')) return;
    try {
        const res = await fetch(`${API}/api/emergency/${sosId}/resolve`, { method: 'PUT' });
        if (res.ok) {
            loadSOSData();
        } else {
            alert('Failed to resolve SOS');
        }
    } catch (e) {
        alert('Error resolving SOS: ' + e.message);
    }
}

// Render SOS history table
function renderSOSHistory(history) {
    const tbody = document.getElementById('sosHistoryBody');
    if (history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:24px; color:#94a3b8;">No SOS history found</td></tr>';
        return;
    }

    tbody.innerHTML = history.map(s => `
        <tr>
            <td><strong>#${s.id}</strong></td>
            <td>${s.user_name || '—'}</td>
            <td>
                <div style="font-size: 12px;">${s.user_email || '—'}</div>
                <div style="font-size: 11px; color: #94a3b8;">${s.user_phone || ''}</div>
            </td>
            <td><span class="badge" style="background:${getBloodBadgeColor(s.blood_group)}">${s.blood_group || '—'}</span></td>
            <td style="font-size: 12px;">${s.latitude?.toFixed(4)}, ${s.longitude?.toFixed(4)}</td>
            <td><span class="badge ${s.status === 'active' ? 'badge-danger' : 'badge-success'}">${s.status}</span></td>
            <td style="font-size: 12px;">${formatSOSDate(s.created_at)}</td>
            <td style="font-size: 12px;">${s.resolved_at ? formatSOSDate(s.resolved_at) : '—'}</td>
            <td>
                ${s.status === 'active' ? `
                    <button class="btn btn-sm btn-success" onclick="resolveSOS(${s.id})">✅ Resolve</button>
                    <button class="btn btn-sm btn-outline" onclick="focusOnSOS(${s.latitude}, ${s.longitude})" style="margin-left:4px;">📍</button>
                ` : `
                    <button class="btn btn-sm btn-outline" onclick="focusOnSOS(${s.latitude}, ${s.longitude})">📍 View</button>
                `}
            </td>
        </tr>
    `).join('');
}

// Filter SOS history
function filterHistory() {
    const q = document.getElementById('sosHistorySearch').value.toLowerCase();
    const filtered = allSOSHistory.filter(s =>
        (s.user_name || '').toLowerCase().includes(q) ||
        (s.user_email || '').toLowerCase().includes(q) ||
        (s.blood_group || '').toLowerCase().includes(q) ||
        s.status.toLowerCase().includes(q)
    );
    renderSOSHistory(filtered);
}

// Auto-refresh toggle
function toggleSOSAutoRefresh() {
    sosAutoRefreshOn = !sosAutoRefreshOn;
    const btn = document.getElementById('sosAutoRefreshBtn');
    if (sosAutoRefreshOn) {
        sosAutoRefreshInterval = setInterval(loadSOSData, 500);
        btn.innerHTML = '⏸️ Auto: ON (0.5s)';
    } else {
        clearInterval(sosAutoRefreshInterval);
        btn.innerHTML = '▶ Auto: OFF';
    }
}

function updateSOSTimestamp() {
    document.getElementById('sosLastUpdate').textContent = 'Updated: ' + new Date().toLocaleTimeString();
}

function getBloodBadgeColor(bg) {
    const colors = { 'A+': '#3b82f6', 'A-': '#2563eb', 'B+': '#22c55e', 'B-': '#16a34a', 'AB+': '#a855f7', 'AB-': '#7c3aed', 'O+': '#f97316', 'O-': '#ea580c' };
    return colors[bg] || '#64748b';
}

function formatSOSDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// Add CSS animation for pulsing markers
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse-marker {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
    }
    .sos-marker { background: transparent !important; border: none !important; }
`;
document.head.appendChild(style);

// Init
initSOSMap();
loadSOSData();
sosAutoRefreshInterval = setInterval(loadSOSData, 500);
