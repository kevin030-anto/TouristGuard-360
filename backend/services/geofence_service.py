import math
from database import get_db


class GeofenceService:
    """Service for danger zone geofencing calculations."""

    @staticmethod
    def haversine_distance(lat1, lng1, lat2, lng2):
        """Calculate distance between two GPS coordinates in kilometers."""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    def check_danger_zones(lat, lng):
        """Check if a coordinate is inside any active danger zone.
        
        Returns:
            list: List of danger zones the point is inside
        """
        db = get_db()
        zones = db.execute(
            'SELECT * FROM danger_zones WHERE is_active = 1'
        ).fetchall()
        db.close()

        triggered_zones = []
        for zone in zones:
            distance = GeofenceService.haversine_distance(
                lat, lng, zone['latitude'], zone['longitude']
            )
            if distance <= zone['radius_km']:
                triggered_zones.append({
                    'id': zone['id'],
                    'name': zone['name'],
                    'description': zone['description'],
                    'severity': zone['severity'],
                    'distance_km': round(distance, 2),
                    'radius_km': zone['radius_km']
                })

        return triggered_zones

    @staticmethod
    def get_users_in_zone(zone_id):
        """Get all active users inside a specific danger zone."""
        db = get_db()
        zone = db.execute(
            'SELECT * FROM danger_zones WHERE id = ?', (zone_id,)
        ).fetchone()

        if not zone:
            db.close()
            return []

        users = db.execute(
            '''SELECT id, full_name, email, last_known_lat, last_known_lng 
               FROM users 
               WHERE is_active = 1 
               AND last_known_lat IS NOT NULL 
               AND last_known_lng IS NOT NULL'''
        ).fetchall()
        db.close()

        affected_users = []
        for user in users:
            distance = GeofenceService.haversine_distance(
                user['last_known_lat'], user['last_known_lng'],
                zone['latitude'], zone['longitude']
            )
            if distance <= zone['radius_km']:
                affected_users.append({
                    'id': user['id'],
                    'name': user['full_name'],
                    'email': user['email'],
                    'distance_km': round(distance, 2)
                })

        return affected_users

    @staticmethod
    def get_users_in_alert_radius(lat, lng, radius_km):
        """Get all active users within a specified radius of a point."""
        db = get_db()
        users = db.execute(
            '''SELECT id, full_name, email, last_known_lat, last_known_lng 
               FROM users 
               WHERE is_active = 1 
               AND last_known_lat IS NOT NULL 
               AND last_known_lng IS NOT NULL'''
        ).fetchall()
        db.close()

        affected_users = []
        for user in users:
            distance = GeofenceService.haversine_distance(
                user['last_known_lat'], user['last_known_lng'],
                lat, lng
            )
            if distance <= radius_km:
                affected_users.append({
                    'id': user['id'],
                    'name': user['full_name'],
                    'email': user['email'],
                    'distance_km': round(distance, 2)
                })

        return affected_users


# Singleton instance
geofence_service = GeofenceService()
