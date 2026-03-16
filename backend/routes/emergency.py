from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import get_current_user
from services.geofence_service import geofence_service
from services.blockchain_service import blockchain

emergency_bp = Blueprint('emergency', __name__, url_prefix='/api/emergency')


@emergency_bp.route('/sos', methods=['POST'])
def trigger_sos():
    """Trigger an SOS emergency alert."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')

    if lat is None or lng is None:
        return jsonify({'error': 'Location coordinates required'}), 400

    db = get_db()

    # Create emergency log
    cursor = db.execute(
        '''INSERT INTO emergency_logs (user_id, latitude, longitude, status)
           VALUES (?, ?, ?, ?)''',
        (user['id'], lat, lng, 'active')
    )
    sos_id = cursor.lastrowid

    # Update user location
    db.execute(
        '''UPDATE users SET last_known_lat = ?, last_known_lng = ?, 
           last_location_update = datetime("now") WHERE id = ?''',
        (lat, lng, user['id'])
    )

    # Log activity
    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user['id'], 'sos_triggered', f'SOS triggered at ({lat}, {lng})')
    )

    db.commit()
    db.close()

    # Blockchain record
    blockchain.record_event('sos_triggered', user_id=user['id'], details={
        'latitude': lat,
        'longitude': lng,
        'sos_id': sos_id,
        'user_name': user['full_name'],
        'blood_group': user['blood_group']
    })

    return jsonify({
        'message': 'SOS alert sent successfully',
        'sos_id': sos_id,
        'user': {
            'name': user['full_name'],
            'blood_group': user['blood_group'],
            'phone': user['phone']
        }
    }), 201


@emergency_bp.route('/active', methods=['GET'])
def get_active_emergencies():
    """Get all active emergency alerts."""
    db = get_db()
    emergencies = db.execute(
        '''SELECT e.*, u.full_name, u.email, u.phone, u.blood_group
           FROM emergency_logs e
           JOIN users u ON e.user_id = u.id
           WHERE e.status = 'active'
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
            'created_at': e['created_at']
        })

    return jsonify(result)


@emergency_bp.route('/<int:sos_id>/resolve', methods=['PUT'])
def resolve_emergency(sos_id):
    """Resolve an emergency."""
    db = get_db()
    db.execute(
        '''UPDATE emergency_logs SET status = 'resolved', resolved_at = datetime("now")
           WHERE id = ?''',
        (sos_id,)
    )
    db.commit()
    db.close()

    blockchain.record_event('sos_resolved', details={'sos_id': sos_id})

    return jsonify({'message': 'Emergency resolved'})
