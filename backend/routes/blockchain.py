from flask import Blueprint, request, jsonify
from services.blockchain_service import blockchain

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api/blockchain')


@blockchain_bp.route('/chain', methods=['GET'])
def get_chain():
    """Get the full blockchain."""
    chain = blockchain.get_chain()
    return jsonify({
        'length': len(chain),
        'chain': chain
    })


@blockchain_bp.route('/verify', methods=['GET'])
def verify_chain():
    """Verify blockchain integrity."""
    result = blockchain.verify_chain()
    return jsonify(result)


@blockchain_bp.route('/latest', methods=['GET'])
def get_latest_block():
    """Get the latest block."""
    chain = blockchain.get_chain()
    if chain:
        return jsonify(chain[-1])
    return jsonify({'error': 'Chain is empty'}), 404
