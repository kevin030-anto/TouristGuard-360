from flask import Blueprint, request, jsonify
import bcrypt
import jwt
from datetime import datetime, timedelta
from config import Config
from database import get_db
from services.blockchain_service import blockchain

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def generate_token(user_id, email):
    """Generate JWT token."""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def verify_token(token):
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """Extract current user from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    if not payload:
        return None
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (payload['user_id'],)).fetchone()
    db.close()
    return user


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    required_fields = ['email', 'password', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    db = get_db()
    
    # Check if email already exists
    existing = db.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'Email already registered'}), 409

    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user
    cursor = db.execute(
        '''INSERT INTO users 
           (email, password_hash, full_name, age, country, blood_group, 
            phone, phone_country_code, 
            emergency_contact_1, emergency_contact_1_code,
            emergency_contact_2, emergency_contact_2_code,
            emergency_contact_3, emergency_contact_3_code,
            auth_provider)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            data['email'], password_hash, data['full_name'],
            data.get('age'), data.get('country'), data.get('blood_group'),
            data.get('phone'), data.get('phone_country_code'),
            data.get('emergency_contact_1'), data.get('emergency_contact_1_code'),
            data.get('emergency_contact_2'), data.get('emergency_contact_2_code'),
            data.get('emergency_contact_3'), data.get('emergency_contact_3_code'),
            'email'
        )
    )
    db.commit()
    user_id = cursor.lastrowid

    # Log activity
    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user_id, 'register', f'User registered with email: {data["email"]}')
    )
    db.commit()
    db.close()

    # Blockchain record
    blockchain.record_event('user_registration', user_id=user_id, details={
        'email': data['email'],
        'name': data['full_name']
    })

    # Generate token
    token = generate_token(user_id, data['email'])

    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': {
            'id': user_id,
            'email': data['email'],
            'full_name': data['full_name']
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password."""
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()

    if not user:
        db.close()
        return jsonify({'error': 'Invalid email or password'}), 401

    # Verify password
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
        db.close()
        return jsonify({'error': 'Invalid email or password'}), 401

    # Update last login
    db.execute(
        'UPDATE users SET last_login = datetime("now") WHERE id = ?',
        (user['id'],)
    )
    # Log activity
    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user['id'], 'login', 'User logged in')
    )
    db.commit()
    db.close()

    token = generate_token(user['id'], user['email'])

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
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
        }
    })


@auth_bp.route('/google', methods=['POST'])
def google_signin():
    """Handle Google Sign-In (mock implementation)."""
    data = request.get_json()

    if not data.get('email') or not data.get('full_name'):
        return jsonify({'error': 'Email and name are required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()

    if user:
        # Existing user - update last login
        db.execute(
            'UPDATE users SET last_login = datetime("now") WHERE id = ?',
            (user['id'],)
        )
        db.commit()
        user_id = user['id']
    else:
        # New user from Google
        cursor = db.execute(
            '''INSERT INTO users (email, full_name, auth_provider, google_id)
               VALUES (?, ?, ?, ?)''',
            (data['email'], data['full_name'], 'google', data.get('google_id', ''))
        )
        db.commit()
        user_id = cursor.lastrowid

        blockchain.record_event('user_registration', user_id=user_id, details={
            'email': data['email'],
            'name': data['full_name'],
            'provider': 'google'
        })

    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user_id, 'login', 'User logged in via Google')
    )
    db.commit()
    db.close()

    token = generate_token(user_id, data['email'])

    return jsonify({
        'message': 'Google sign-in successful',
        'token': token,
        'user': {
            'id': user_id,
            'email': data['email'],
            'full_name': data['full_name']
        }
    })


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get current user profile."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

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
        'created_at': user['created_at']
    })


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    db = get_db()

    db.execute(
        '''UPDATE users SET 
           full_name = COALESCE(?, full_name),
           age = COALESCE(?, age),
           country = COALESCE(?, country),
           blood_group = COALESCE(?, blood_group),
           phone = COALESCE(?, phone),
           phone_country_code = COALESCE(?, phone_country_code),
           emergency_contact_1 = COALESCE(?, emergency_contact_1),
           emergency_contact_1_code = COALESCE(?, emergency_contact_1_code),
           emergency_contact_2 = COALESCE(?, emergency_contact_2),
           emergency_contact_2_code = COALESCE(?, emergency_contact_2_code),
           emergency_contact_3 = COALESCE(?, emergency_contact_3),
           emergency_contact_3_code = COALESCE(?, emergency_contact_3_code)
           WHERE id = ?''',
        (
            data.get('full_name'), data.get('age'), data.get('country'),
            data.get('blood_group'), data.get('phone'), data.get('phone_country_code'),
            data.get('emergency_contact_1'), data.get('emergency_contact_1_code'),
            data.get('emergency_contact_2'), data.get('emergency_contact_2_code'),
            data.get('emergency_contact_3'), data.get('emergency_contact_3_code'),
            user['id']
        )
    )
    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user['id'], 'profile_update', 'User updated profile')
    )
    db.commit()
    db.close()

    return jsonify({'message': 'Profile updated successfully'})


@auth_bp.route('/delete-account', methods=['DELETE'])
def delete_account():
    """Delete user account - removes documents and logs, retains basic identity."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()

    # Delete documents
    db.execute('DELETE FROM documents WHERE user_id = ?', (user['id'],))

    # Delete activity logs
    db.execute('DELETE FROM activity_logs WHERE user_id = ?', (user['id'],))

    # Mark user as inactive but retain basic info
    db.execute(
        '''UPDATE users SET 
           is_active = 0, 
           password_hash = NULL,
           last_known_lat = NULL,
           last_known_lng = NULL
           WHERE id = ?''',
        (user['id'],)
    )

    db.commit()
    db.close()

    blockchain.record_event('account_deleted', user_id=user['id'], details={
        'email': user['email']
    })

    return jsonify({'message': 'Account deleted. Basic identity retained for records.'})


@auth_bp.route('/location', methods=['POST'])
def update_location():
    """Update user's current location."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data.get('latitude') or not data.get('longitude'):
        return jsonify({'error': 'Latitude and longitude required'}), 400

    db = get_db()
    db.execute(
        '''UPDATE users SET 
           last_known_lat = ?, last_known_lng = ?, 
           last_location_update = datetime("now")
           WHERE id = ?''',
        (data['latitude'], data['longitude'], user['id'])
    )
    db.commit()
    db.close()

    # Check danger zones
    from services.geofence_service import geofence_service
    triggered_zones = geofence_service.check_danger_zones(data['latitude'], data['longitude'])

    return jsonify({
        'message': 'Location updated',
        'danger_zones': triggered_zones
    })
