from flask import Blueprint, request, jsonify
from database import get_db
from services.geofence_service import geofence_service
from services.blockchain_service import blockchain

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')


@alerts_bp.route('', methods=['GET'])
def get_alerts():
    """Get active alerts. Optionally filter by user location (10km radius)."""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    db = get_db()
    alerts = db.execute(
        'SELECT * FROM alerts WHERE is_active = 1 ORDER BY created_at DESC'
    ).fetchall()
    db.close()

    result = []
    for alert in alerts:
        alert_data = {
            'id': alert['id'],
            'name': alert['name'],
            'alert_type': alert['alert_type'],
            'description': alert['description'],
            'latitude': alert['latitude'],
            'longitude': alert['longitude'],
            'radius_km': alert['radius_km'],
            'severity': alert['severity'],
            'created_at': alert['created_at']
        }

        # If user location provided, only include alerts within radius
        if lat is not None and lng is not None:
            distance = geofence_service.haversine_distance(
                lat, lng, alert['latitude'], alert['longitude']
            )
            if distance <= alert['radius_km']:
                alert_data['distance_km'] = round(distance, 2)
                result.append(alert_data)
        else:
            result.append(alert_data)

    return jsonify(result)


@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert."""
    db = get_db()
    alert = db.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,)).fetchone()
    db.close()

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify({
        'id': alert['id'],
        'name': alert['name'],
        'alert_type': alert['alert_type'],
        'description': alert['description'],
        'latitude': alert['latitude'],
        'longitude': alert['longitude'],
        'radius_km': alert['radius_km'],
        'severity': alert['severity'],
        'created_at': alert['created_at']
    })
