import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from database import init_db

socketio = SocketIO()

def create_app():
    app = Flask(__name__,
                template_folder='admin/templates',
                static_folder='admin/static')
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, origins=Config.CORS_ORIGINS)

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Initialize database
    init_db()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.emergency import emergency_bp
    from routes.alerts import alerts_bp
    from routes.notifications import notifications_bp
    from routes.danger_zones import danger_zones_bp
    from routes.documents import documents_bp
    from routes.transport import transport_bp
    from routes.blockchain import blockchain_bp
    from routes.admin import admin_bp, admin_views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(emergency_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(danger_zones_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(transport_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_views_bp)

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'TouristGuard360 Backend is running'}

    # SocketIO events
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('location_update')
    def handle_location_update(data):
        socketio.emit('user_location_update', data, broadcast=True)

    @socketio.on('sos_alert')
    def handle_sos(data):
        socketio.emit('sos_notification', data, broadcast=True)

    # Initialize SocketIO with app (use threading for Windows compatibility)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 60)
    print("  TouristGuard360 — Backend Server")
    print("=" * 60)
    print(f"  API:    http://localhost:5000/api/")
    print(f"  Admin:  http://localhost:5000/admin/")
    print(f"  Health: http://localhost:5000/api/health")
    print("=" * 60 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
