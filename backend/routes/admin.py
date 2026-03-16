from flask import Blueprint, request, jsonify, render_template
import bcrypt
from database import get_db
from services.blockchain_service import blockchain
from services.geofence_service import geofence_service
from app import socketio

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
admin_views_bp = Blueprint('admin_views', __name__, 
                           url_prefix='/admin',
                           template_folder='admin/templates',
                           static_folder='admin/static')


# ========== Admin Web Views ==========

@admin_views_bp.route('/')
@admin_views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@admin_views_bp.route('/alerts')
def alerts_page():
    return render_template('alerts.html')

@admin_views_bp.route('/danger-zones')
def danger_zones_page():
    return render_template('danger_zones.html')

@admin_views_bp.route('/monitoring')
def monitoring_page():
    return render_template('monitoring.html')

@admin_views_bp.route('/sos-monitor')
def sos_monitor_page():
    return render_template('sos_monitor.html')


# ========== Admin API: User Management ==========

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all registered users."""
    db = get_db()
    users = db.execute(
        'SELECT * FROM users ORDER BY created_at DESC'
    ).fetchall()

    result = []
    for u in users:
        doc_count = db.execute(
            'SELECT COUNT(*) as count FROM documents WHERE user_id = ?', (u['id'],)
        ).fetchone()['count']

        result.append({
            'id': u['id'],
            'email': u['email'],
            'full_name': u['full_name'],
            'age': u['age'],
            'country': u['country'],
            'blood_group': u['blood_group'],
            'phone': u['phone'],
            'phone_country_code': u['phone_country_code'],
            'emergency_contact_1': u['emergency_contact_1'],
            'emergency_contact_1_code': u['emergency_contact_1_code'],
            'emergency_contact_2': u['emergency_contact_2'],
            'emergency_contact_2_code': u['emergency_contact_2_code'],
            'emergency_contact_3': u['emergency_contact_3'],
            'emergency_contact_3_code': u['emergency_contact_3_code'],
            'auth_provider': u['auth_provider'],
            'last_known_lat': u['last_known_lat'],
            'last_known_lng': u['last_known_lng'],
            'is_active': u['is_active'],
            'document_count': doc_count,
            'created_at': u['created_at'],
            'last_login': u['last_login']
        })
    db.close()

    return jsonify(result)


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    """Get detailed user info including alert history."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404

    doc_count = db.execute(
        'SELECT COUNT(*) as count FROM documents WHERE user_id = ?', (user_id,)
    ).fetchone()['count']

    alerts = db.execute(
        '''SELECT * FROM activity_logs 
           WHERE user_id = ? 
           ORDER BY created_at DESC LIMIT 50''',
        (user_id,)
    ).fetchall()

    emergency_history = db.execute(
        '''SELECT * FROM emergency_logs 
           WHERE user_id = ? ORDER BY created_at DESC''',
        (user_id,)
    ).fetchall()

    db.close()

    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'full_name': user['full_name'],
        'age': user['age'],
        'country': user['country'],
        'blood_group': user['blood_group'],
        'phone': user['phone'],
        'phone_country_code': user['phone_country_code'],
        'emergency_contact_1': user['emergency_contact_1'],
        'emergency_contact_1_code': user['emergency_contact_1_code'],
        'emergency_contact_2': user['emergency_contact_2'],
        'emergency_contact_2_code': user['emergency_contact_2_code'],
        'emergency_contact_3': user['emergency_contact_3'],
        'emergency_contact_3_code': user['emergency_contact_3_code'],
        'auth_provider': user['auth_provider'],
        'last_known_lat': user['last_known_lat'],
        'last_known_lng': user['last_known_lng'],
        'is_active': user['is_active'],
        'document_count': doc_count,
        'created_at': user['created_at'],
        'last_login': user['last_login'],
        'activity_log': [{'action': a['action'], 'details': a['details'], 'created_at': a['created_at']} for a in alerts],
        'emergency_history': [{'id': e['id'], 'lat': e['latitude'], 'lng': e['longitude'], 'status': e['status'], 'created_at': e['created_at']} for e in emergency_history]
    })


@admin_bp.route('/users', methods=['POST'])
def add_user():
    """Admin adds a new user."""
    data = request.get_json()
    if not data.get('email') or not data.get('full_name') or not data.get('password'):
        return jsonify({'error': 'Email, name, and password required'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'Email already exists'}), 409

    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor = db.execute(
        '''INSERT INTO users (email, password_hash, full_name, age, country, blood_group, phone, phone_country_code)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (data['email'], password_hash, data['full_name'],
         data.get('age'), data.get('country'), data.get('blood_group'),
         data.get('phone'), data.get('phone_country_code'))
    )
    db.commit()
    user_id = cursor.lastrowid
    db.close()

    return jsonify({'message': 'User created', 'id': user_id}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    """Admin edits a user."""
    data = request.get_json()
    db = get_db()

    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404

    # If password is provided, hash it
    if data.get('password'):
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))

    db.execute(
        '''UPDATE users SET
           full_name = COALESCE(?, full_name),
           age = COALESCE(?, age),
           country = COALESCE(?, country),
           blood_group = COALESCE(?, blood_group),
           phone = COALESCE(?, phone),
           email = COALESCE(?, email)
           WHERE id = ?''',
        (data.get('full_name'), data.get('age'), data.get('country'),
         data.get('blood_group'), data.get('phone'), data.get('email'), user_id)
    )
    db.commit()
    db.close()

    return jsonify({'message': 'User updated'})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Admin deletes a user."""
    db = get_db()
    db.execute('DELETE FROM documents WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM activity_logs WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM emergency_logs WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    db.close()

    return jsonify({'message': 'User deleted'})


# ========== Admin API: Alert Management ==========

@admin_bp.route('/alerts', methods=['GET'])
def admin_get_alerts():
    """Get all alerts."""
    db = get_db()
    alerts = db.execute('SELECT * FROM alerts ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([{
        'id': a['id'], 'name': a['name'], 'alert_type': a['alert_type'],
        'description': a['description'], 'latitude': a['latitude'],
        'longitude': a['longitude'], 'radius_km': a['radius_km'],
        'severity': a['severity'], 'is_active': a['is_active'],
        'created_at': a['created_at']
    } for a in alerts])


@admin_bp.route('/alerts', methods=['POST'])
def admin_create_alert():
    """Create a new alert. Always returns JSON (never HTML)."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    required = ['name', 'alert_type', 'latitude', 'longitude']
    for field in required:
        if data.get(field) is None:
            return jsonify({'error': f'{field} is required'}), 400
    try:
        db = get_db()
        cursor = db.execute(
            '''INSERT INTO alerts (name, alert_type, description, latitude, longitude, radius_km, severity)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['alert_type'], data.get('description', ''),
             float(data['latitude']), float(data['longitude']),
             float(data.get('radius_km', 10)), data.get('severity', 'warning'))
        )
        alert_id = cursor.lastrowid
        db.commit()
        db.close()
    except Exception as e:
        return jsonify({'error': 'Failed to create alert', 'detail': str(e)}), 500

    try:
        affected = geofence_service.get_users_in_alert_radius(
            float(data['latitude']), float(data['longitude']),
            float(data.get('radius_km', 10))
        )
    except Exception:
        affected = []

    try:
        blockchain.record_event(
            'alert_created',
            details={
                'alert_id': alert_id,
                'name': data['name'],
                'type': data['alert_type'],
                'affected_users': len(affected),
            },
        )
    except Exception:
        pass

    try:
        socketio.emit(
            'alert_created',
            {
                'id': alert_id,
                'name': data['name'],
                'alert_type': data['alert_type'],
                'description': data.get('description', ''),
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'radius_km': data.get('radius_km', 10),
                'severity': data.get('severity', 'warning'),
            },
            broadcast=True,
        )
    except Exception:
        pass

    return jsonify({
        'message': 'Alert created',
        'id': alert_id,
        'affected_users': len(affected),
        'users': affected
    }), 201


@admin_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def admin_update_alert(alert_id):
    """Update an alert."""
    data = request.get_json()
    db = get_db()
    db.execute(
        '''UPDATE alerts SET
           name = COALESCE(?, name),
           alert_type = COALESCE(?, alert_type),
           description = COALESCE(?, description),
           latitude = COALESCE(?, latitude),
           longitude = COALESCE(?, longitude),
           radius_km = COALESCE(?, radius_km),
           severity = COALESCE(?, severity),
           is_active = COALESCE(?, is_active),
           updated_at = datetime("now")
           WHERE id = ?''',
        (data.get('name'), data.get('alert_type'), data.get('description'),
         data.get('latitude'), data.get('longitude'), data.get('radius_km'),
         data.get('severity'), data.get('is_active'), alert_id)
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Alert updated'})


@admin_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def admin_delete_alert(alert_id):
    """Delete an alert."""
    db = get_db()
    db.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Alert deleted'})


# ========== Admin API: Notification Management ==========

@admin_bp.route('/notifications', methods=['GET'])
def admin_get_notifications():
    """Get all notifications."""
    db = get_db()
    notifs = db.execute('SELECT * FROM notifications ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([{
        'id': n['id'], 'name': n['name'], 'description': n['description'],
        'start_date': n['start_date'], 'end_date': n['end_date'],
        'is_active': n['is_active'], 'is_done': n['is_done'],
        'created_at': n['created_at']
    } for n in notifs])


@admin_bp.route('/notifications', methods=['POST'])
def admin_create_notification():
    """Create a new notification."""
    data = request.get_json()
    required = ['name', 'description', 'start_date', 'end_date']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    db = get_db()
    cursor = db.execute(
        '''INSERT INTO notifications (name, description, start_date, end_date)
           VALUES (?, ?, ?, ?)''',
        (data['name'], data['description'], data['start_date'], data['end_date'])
    )
    db.commit()
    notif_id = cursor.lastrowid
    db.close()

    # Broadcast real-time notification event
    socketio.emit(
        'notification_created',
        {
            'id': notif_id,
            'name': data['name'],
            'description': data['description'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
        },
        broadcast=True,
    )

    return jsonify({'message': 'Notification created', 'id': notif_id}), 201


@admin_bp.route('/notifications/<int:notif_id>', methods=['PUT'])
def admin_update_notification(notif_id):
    """Update a notification."""
    data = request.get_json()
    db = get_db()
    db.execute(
        '''UPDATE notifications SET
           name = COALESCE(?, name),
           description = COALESCE(?, description),
           start_date = COALESCE(?, start_date),
           end_date = COALESCE(?, end_date),
           is_active = COALESCE(?, is_active),
           is_done = COALESCE(?, is_done)
           WHERE id = ?''',
        (data.get('name'), data.get('description'),
         data.get('start_date'), data.get('end_date'),
         data.get('is_active'), data.get('is_done'), notif_id)
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Notification updated'})


@admin_bp.route('/notifications/<int:notif_id>', methods=['DELETE'])
def admin_delete_notification(notif_id):
    """Delete a notification."""
    db = get_db()
    db.execute('DELETE FROM notifications WHERE id = ?', (notif_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Notification deleted'})


@admin_bp.route('/notifications/<int:notif_id>/done', methods=['POST'])
def admin_mark_notification_done(notif_id):
    """Mark a notification as done."""
    db = get_db()
    db.execute(
        'UPDATE notifications SET is_done = 1, is_active = 0 WHERE id = ?',
        (notif_id,)
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Notification marked as done'})


# ========== Admin API: Danger Zone Management ==========

@admin_bp.route('/danger-zones', methods=['GET'])
def admin_get_danger_zones():
    """Get all danger zones."""
    db = get_db()
    zones = db.execute('SELECT * FROM danger_zones ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([{
        'id': z['id'], 'name': z['name'], 'description': z['description'],
        'latitude': z['latitude'], 'longitude': z['longitude'],
        'radius_km': z['radius_km'], 'severity': z['severity'],
        'is_active': z['is_active'], 'created_at': z['created_at']
    } for z in zones])


@admin_bp.route('/danger-zones', methods=['POST'])
def admin_create_danger_zone():
    """Create a new danger zone."""
    data = request.get_json()
    required = ['name', 'latitude', 'longitude', 'radius_km']
    for field in required:
        if data.get(field) is None:
            return jsonify({'error': f'{field} is required'}), 400

    db = get_db()
    cursor = db.execute(
        '''INSERT INTO danger_zones (name, description, latitude, longitude, radius_km, severity)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data['name'], data.get('description', ''),
         data['latitude'], data['longitude'],
         data['radius_km'], data.get('severity', 'high'))
    )
    zone_id = cursor.lastrowid
    db.commit()
    db.close()

    blockchain.record_event('danger_zone_created', details={
        'zone_id': zone_id,
        'name': data['name'],
        'radius_km': data['radius_km']
    })

    return jsonify({'message': 'Danger zone created', 'id': zone_id}), 201


@admin_bp.route('/danger-zones/<int:zone_id>', methods=['PUT'])
def admin_update_danger_zone(zone_id):
    """Update a danger zone."""
    data = request.get_json()
    db = get_db()
    db.execute(
        '''UPDATE danger_zones SET
           name = COALESCE(?, name),
           description = COALESCE(?, description),
           latitude = COALESCE(?, latitude),
           longitude = COALESCE(?, longitude),
           radius_km = COALESCE(?, radius_km),
           severity = COALESCE(?, severity),
           is_active = COALESCE(?, is_active),
           updated_at = datetime("now")
           WHERE id = ?''',
        (data.get('name'), data.get('description'),
         data.get('latitude'), data.get('longitude'),
         data.get('radius_km'), data.get('severity'),
         data.get('is_active'), zone_id)
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Danger zone updated'})


@admin_bp.route('/danger-zones/<int:zone_id>', methods=['DELETE'])
def admin_delete_danger_zone(zone_id):
    """Delete a danger zone."""
    db = get_db()
    db.execute('DELETE FROM danger_zones WHERE id = ?', (zone_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Danger zone deleted'})


# ========== Admin API: Active User Monitoring ==========

@admin_bp.route('/active-users', methods=['GET'])
def get_active_users():
    """Get all active users with their last known locations."""
    db = get_db()
    users = db.execute(
        '''SELECT id, full_name, email, last_known_lat, last_known_lng, 
           last_location_update, is_active
           FROM users 
           WHERE is_active = 1 
           AND last_known_lat IS NOT NULL'''
    ).fetchall()
    db.close()

    result = []
    for u in users:
        # Check if user is in any danger zone
        in_danger = []
        if u['last_known_lat'] and u['last_known_lng']:
            in_danger = geofence_service.check_danger_zones(
                u['last_known_lat'], u['last_known_lng']
            )

        result.append({
            'id': u['id'],
            'name': u['full_name'],
            'email': u['email'],
            'latitude': u['last_known_lat'],
            'longitude': u['last_known_lng'],
            'last_update': u['last_location_update'],
            'in_danger_zones': in_danger
        })

    return jsonify(result)


# ========== Admin API: Dashboard Stats ==========

@admin_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    db = get_db()

    total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    active_users = db.execute(
        'SELECT COUNT(*) as count FROM users WHERE is_active = 1 AND last_known_lat IS NOT NULL'
    ).fetchone()['count']
    active_alerts = db.execute(
        'SELECT COUNT(*) as count FROM alerts WHERE is_active = 1'
    ).fetchone()['count']
    danger_zones = db.execute(
        'SELECT COUNT(*) as count FROM danger_zones WHERE is_active = 1'
    ).fetchone()['count']
    active_sos = db.execute(
        "SELECT COUNT(*) as count FROM emergency_logs WHERE status = 'active'"
    ).fetchone()['count']
    resolved_sos = db.execute(
        "SELECT COUNT(*) as count FROM emergency_logs WHERE status = 'resolved'"
    ).fetchone()['count']
    total_documents = db.execute(
        'SELECT COUNT(*) as count FROM documents'
    ).fetchone()['count']

    db.close()

    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'active_alerts': active_alerts,
        'danger_zones': danger_zones,
        'active_sos': active_sos,
        'resolved_sos': resolved_sos,
        'total_documents': total_documents
    })


# ========== Admin API: SOS History ==========

@admin_bp.route('/sos-history', methods=['GET'])
def get_sos_history():
    """Get complete SOS emergency history."""
    db = get_db()
    emergencies = db.execute(
        '''SELECT e.*, u.full_name, u.email, u.phone, u.blood_group
           FROM emergency_logs e
           JOIN users u ON e.user_id = u.id
           ORDER BY e.created_at DESC'''
    ).fetchall()
    db.close()

    result = []
    for e in emergencies:
        result.append({
            'id': e['id'],
            'user_id': e['user_id'],
            'user_name': e['full_name'],
            'user_email': e['email'],
            'user_phone': e['phone'],
            'blood_group': e['blood_group'],
            'latitude': e['latitude'],
            'longitude': e['longitude'],
            'status': e['status'],
            'created_at': e['created_at'],
            'resolved_at': e['resolved_at']
        })

    return jsonify(result)
