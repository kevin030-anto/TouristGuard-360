from flask import Blueprint, request, jsonify
from database import get_db

danger_zones_bp = Blueprint('danger_zones', __name__, url_prefix='/api/danger-zones')


@danger_zones_bp.route('', methods=['GET'])
def get_danger_zones():
    """Get all active danger zones."""
    db = get_db()
    zones = db.execute(
        'SELECT * FROM danger_zones WHERE is_active = 1 ORDER BY created_at DESC'
    ).fetchall()
    db.close()

    result = []
    for z in zones:
        result.append({
            'id': z['id'],
            'name': z['name'],
            'description': z['description'],
            'latitude': z['latitude'],
            'longitude': z['longitude'],
            'radius_km': z['radius_km'],
            'severity': z['severity'],
            'created_at': z['created_at']
        })

    return jsonify(result)


@danger_zones_bp.route('/check', methods=['POST'])
def check_zones():
    """Check if a coordinate is inside any danger zone."""
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')

    if lat is None or lng is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    from services.geofence_service import geofence_service
    triggered = geofence_service.check_danger_zones(lat, lng)

    return jsonify({
        'in_danger_zone': len(triggered) > 0,
        'zones': triggered
    })
