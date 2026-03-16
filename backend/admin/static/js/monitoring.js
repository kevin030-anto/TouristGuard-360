// Live Monitoring JavaScript
const API = '';
let monMap = null;
let userMarkers = [];
let dangerZoneCircles = [];
let autoRefreshInterval = null;
let isAutoRefresh = false;

function initMap() {
    monMap = L.map('monitoringMap').setView([20.5937, 78.9629], 5);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(monMap);
}

async function refreshData() {
    await Promise.all([loadActiveUsers(), loadDangerZones(), loadStats()]);
}

async function loadStats() {
    try {
        const res = await fetch(`${API}/api/admin/dashboard-stats`);
        const data = await res.json();
        document.getElementById('monActiveSOS').textContent = data.active_sos;
    } catch (e) { }
}

async function loadActiveUsers() {
    try {
        const res = await fetch(`${API}/api/admin/active-users`);
        const users = await res.json();

        // Clear existing markers
        userMarkers.forEach(m => monMap.removeLayer(m));
        userMarkers = [];

        let usersInDanger = 0;
        const tbody = document.getElementById('monitoringTableBody');

        document.getElementById('monActiveUsers').textContent = users.length;

        tbody.innerHTML = users.map(u => {
            const inDanger = u.in_danger_zones && u.in_danger_zones.length > 0;
            if (inDanger) usersInDanger++;

            // Add marker to map
            const icon = L.divIcon({
                className: 'user-marker',
                html: `<div style="
                    background: ${inDanger ? '#ef4444' : '#3b82f6'};
                    width: 12px; height: 12px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 0 6px ${inDanger ? '#ef4444' : '#3b82f6'};
                "></div>`,
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });

            if (u.latitude && u.longitude) {
                const marker = L.marker([u.latitude, u.longitude], { icon })
                    .addTo(monMap)
                    .bindPopup(`<strong>${u.name}</strong><br>${u.email}<br>${inDanger ? '⚠️ IN DANGER ZONE' : '✅ Safe'}`);
                userMarkers.push(marker);
            }

            return `<tr>
                <td><strong>${u.name}</strong></td>
                <td>${u.email}</td>
                <td>${u.latitude ? `${u.latitude.toFixed(4)}, ${u.longitude.toFixed(4)}` : '—'}</td>
                <td>${u.last_update || '—'}</td>
                <td>${inDanger
                    ? `<span class="badge badge-danger pulse">⚠️ In Danger Zone</span>`
                    : `<span class="badge badge-success">✅ Safe</span>`}</td>
            </tr>`;
        }).join('') || '<tr><td colspan="5">No active users</td></tr>';

        document.getElementById('monUsersInDanger').textContent = usersInDanger;

        // Fit map to markers
        if (userMarkers.length > 0) {
            const group = new L.featureGroup(userMarkers);
            monMap.fitBounds(group.getBounds().pad(0.2));
        }
    } catch (e) {
        console.error('Failed to load active users:', e);
    }
}

async function loadDangerZones() {
    try {
        const res = await fetch(`${API}/api/admin/danger-zones`);
        const zones = await res.json();

        dangerZoneCircles.forEach(c => monMap.removeLayer(c));
        dangerZoneCircles = [];

        zones.forEach(z => {
            const color = z.severity === 'extreme' ? '#ef4444' : z.severity === 'high' ? '#f59e0b' : '#3b82f6';
            const circle = L.circle([z.latitude, z.longitude], {
                radius: z.radius_km * 1000,
                color: color,
                fillColor: color,
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5,5'
            }).addTo(monMap);
            circle.bindPopup(`<strong>⚠️ ${z.name}</strong><br>Radius: ${z.radius_km} km`);
            dangerZoneCircles.push(circle);
        });
    } catch (e) {
        console.error('Failed to load danger zones:', e);
    }
}

function toggleAutoRefresh() {
    isAutoRefresh = !isAutoRefresh;
    const btn = document.getElementById('autoRefreshBtn');
    if (isAutoRefresh) {
        btn.textContent = '⏸ Auto-Refresh: ON (0.5s)';
        btn.classList.remove('btn-success');
        btn.classList.add('btn-danger');
        autoRefreshInterval = setInterval(refreshData, 500);
    } else {
        btn.textContent = '▶ Auto-Refresh: OFF';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-success');
        clearInterval(autoRefreshInterval);
    }
}

// Init
initMap();
refreshData();
// Start auto-refresh ON by default
toggleAutoRefresh();

