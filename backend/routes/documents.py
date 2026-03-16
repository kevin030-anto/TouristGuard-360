import os
import uuid
from flask import Blueprint, request, jsonify, send_file
from database import get_db
from routes.auth import get_current_user
from services.encryption_service import encryption_service
from config import Config

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and encrypt a document."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Read file data
    file_data = file.read()
    file_size = len(file_data)
    file_ext = file.filename.rsplit('.', 1)[1].lower()

    # Generate unique stored filename
    stored_filename = f"{uuid.uuid4().hex}.enc"
    stored_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Encrypt and save
    encryption_service.encrypt_file_to_disk(file_data, stored_path)

    # Save metadata to database
    category = request.form.get('category', 'other')
    db = get_db()
    cursor = db.execute(
        '''INSERT INTO documents (user_id, original_filename, stored_filename, file_type, file_size, category)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user['id'], file.filename, stored_filename, file_ext, file_size, category)
    )
    doc_id = cursor.lastrowid

    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user['id'], 'document_upload', f'Uploaded: {file.filename}')
    )
    db.commit()
    db.close()

    return jsonify({
        'message': 'Document uploaded successfully',
        'document': {
            'id': doc_id,
            'filename': file.filename,
            'file_type': file_ext,
            'file_size': file_size,
            'category': category
        }
    }), 201


@documents_bp.route('', methods=['GET'])
def list_documents():
    """List user's documents (metadata only)."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    docs = db.execute(
        'SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC',
        (user['id'],)
    ).fetchall()
    db.close()

    result = []
    for doc in docs:
        result.append({
            'id': doc['id'],
            'filename': doc['original_filename'],
            'file_type': doc['file_type'],
            'file_size': doc['file_size'],
            'category': doc['category'],
            'uploaded_at': doc['uploaded_at']
        })

    return jsonify(result)


@documents_bp.route('/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """Download and decrypt a document."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    doc = db.execute(
        'SELECT * FROM documents WHERE id = ? AND user_id = ?',
        (doc_id, user['id'])
    ).fetchone()
    db.close()

    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    stored_path = os.path.join(Config.UPLOAD_FOLDER, doc['stored_filename'])
    if not os.path.exists(stored_path):
        return jsonify({'error': 'File not found on disk'}), 404

    # Decrypt
    decrypted_data = encryption_service.decrypt_file_from_disk(stored_path)

    # Create temp file for download
    import tempfile
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, doc['original_filename'])
    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True, download_name=doc['original_filename'])


@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    doc = db.execute(
        'SELECT * FROM documents WHERE id = ? AND user_id = ?',
        (doc_id, user['id'])
    ).fetchone()

    if not doc:
        db.close()
        return jsonify({'error': 'Document not found'}), 404

    # Delete encrypted file
    stored_path = os.path.join(Config.UPLOAD_FOLDER, doc['stored_filename'])
    if os.path.exists(stored_path):
        os.remove(stored_path)

    # Delete from database
    db.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    db.execute(
        'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
        (user['id'], 'document_delete', f'Deleted: {doc["original_filename"]}')
    )
    db.commit()
    db.close()

    return jsonify({'message': 'Document deleted successfully'})
