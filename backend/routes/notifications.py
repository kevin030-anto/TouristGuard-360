from flask import Blueprint, request, jsonify
from database import get_db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """Get active, non-expired notifications."""
    db = get_db()
    notifications = db.execute(
        '''SELECT * FROM notifications 
           WHERE is_active = 1 AND is_done = 0
           AND date(end_date) >= date('now')
           ORDER BY created_at DESC'''
    ).fetchall()
    db.close()

    result = []
    for n in notifications:
        result.append({
            'id': n['id'],
            'name': n['name'],
            'description': n['description'],
            'start_date': n['start_date'],
            'end_date': n['end_date'],
            'created_at': n['created_at']
        })

    return jsonify(result)


@notifications_bp.route('/<int:notif_id>', methods=['GET'])
def get_notification(notif_id):
    """Get a specific notification."""
    db = get_db()
    n = db.execute('SELECT * FROM notifications WHERE id = ?', (notif_id,)).fetchone()
    db.close()

    if not n:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({
        'id': n['id'],
        'name': n['name'],
        'description': n['description'],
        'start_date': n['start_date'],
        'end_date': n['end_date'],
        'created_at': n['created_at']
    })
