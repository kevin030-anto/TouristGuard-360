// Danger Zones JavaScript
const API = '';
let allZones = [];
let mainMap = null;
let formMap = null;
let formMarker = null;
let formCircle = null;
let zoneCircles = [];

async function loadZones() {
    try {
        const res = await fetch(`${API}/api/admin/danger-zones`);
        allZones = await res.json();
        renderZones(allZones);
        renderZonesOnMap(allZones);
    } catch (e) { console.error('Failed to load zones:', e); }
}

function renderZones(zones) {
    const tbody = document.getElementById('zonesTableBody');
    tbody.innerHTML = zones.map(z => `
        <tr>
            <td><strong>${z.name}</strong><br><small style="color: var(--text-muted);">${z.description || ''}</small></td>
            <td>${z.radius_km} km</td>
            <td><span class="badge badge-${z.severity === 'extreme' ? 'danger' : z.severity === 'high' ? 'warning' : 'info'}">${z.severity}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="editZone(${z.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteZone(${z.id})" style="margin-left:4px;">🗑️</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="4">No danger zones defined</td></tr>';
}

function initMainMap() {
    if (mainMap) return;
    mainMap = L.map('dangerZoneMap').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(mainMap);
}

function renderZonesOnMap(zones) {
    // Clear existing
    zoneCircles.forEach(c => mainMap.removeLayer(c));
    zoneCircles = [];

    zones.forEach(z => {
        const color = z.severity === 'extreme' ? '#ef4444' : z.severity === 'high' ? '#f59e0b' : '#3b82f6';
        const circle = L.circle([z.latitude, z.longitude], {
            radius: z.radius_km * 1000,
            color: color,
            fillColor: color,
            fillOpacity: 0.2,
            weight: 2
        }).addTo(mainMap);
        circle.bindPopup(`<strong>${z.name}</strong><br>Radius: ${z.radius_km} km<br>Severity: ${z.severity}`);
        zoneCircles.push(circle);
    });

    if (zones.length > 0) {
        const group = new L.featureGroup(zoneCircles);
        mainMap.fitBounds(group.getBounds().pad(0.1));
    }
}

function showZoneForm(zone = null) {
    document.getElementById('zoneFormTitle').textContent = zone ? 'Edit Danger Zone' : 'Add Danger Zone';
    document.getElementById('editZoneId').value = zone ? zone.id : '';
    document.getElementById('zoneName').value = zone ? zone.name : '';
    document.getElementById('zoneDescription').value = zone ? zone.description || '' : '';
    document.getElementById('zoneLat').value = zone ? zone.latitude : '';
    document.getElementById('zoneLng').value = zone ? zone.longitude : '';
    document.getElementById('zoneRadius').value = zone ? zone.radius_km : 5;
    document.getElementById('zoneSeverity').value = zone ? zone.severity : 'high';
    document.getElementById('zoneFormModal').classList.remove('hidden');

    setTimeout(() => {
        if (!formMap) {
            formMap = L.map('zoneFormMap').setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(formMap);
            formMap.on('click', function (e) {
                document.getElementById('zoneLat').value = e.latlng.lat.toFixed(6);
                document.getElementById('zoneLng').value = e.latlng.lng.toFixed(6);
                updateFormMarker(e.latlng.lat, e.latlng.lng);
            });
        }
        formMap.invalidateSize();
        if (zone) {
            formMap.setView([zone.latitude, zone.longitude], 10);
            updateFormMarker(zone.latitude, zone.longitude);
        }
    }, 200);
}

function updateFormMarker(lat, lng) {
    if (formMarker) formMap.removeLayer(formMarker);
    if (formCircle) formMap.removeLayer(formCircle);
    formMarker = L.marker([lat, lng]).addTo(formMap);
    const radius = parseFloat(document.getElementById('zoneRadius').value) || 5;
    formCircle = L.circle([lat, lng], { radius: radius * 1000, color: '#f59e0b', fillOpacity: 0.2 }).addTo(formMap);
}

function editZone(id) {
    const zone = allZones.find(z => z.id === id);
    if (zone) showZoneForm(zone);
}

async function saveZone() {
    const editId = document.getElementById('editZoneId').value;
    const body = {
        name: document.getElementById('zoneName').value,
        description: document.getElementById('zoneDescription').value,
        latitude: parseFloat(document.getElementById('zoneLat').value),
        longitude: parseFloat(document.getElementById('zoneLng').value),
        radius_km: parseFloat(document.getElementById('zoneRadius').value),
        severity: document.getElementById('zoneSeverity').value
    };
    if (!body.name || isNaN(body.latitude) || isNaN(body.longitude)) {
        alert('Please fill required fields and select location on map'); return;
    }
    try {
        const url = editId ? `${API}/api/admin/danger-zones/${editId}` : `${API}/api/admin/danger-zones`;
        const res = await fetch(url, {
            method: editId ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) { const d = await res.json(); alert(d.error || 'Failed'); return; }
        closeModal('zoneFormModal');
        loadZones();
    } catch (e) { alert('Error: ' + e.message); }
}

async function deleteZone(id) {
    if (!confirm('Delete this danger zone?')) return;
    await fetch(`${API}/api/admin/danger-zones/${id}`, { method: 'DELETE' });
    loadZones();
}

function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// Init
initMainMap();
loadZones();
