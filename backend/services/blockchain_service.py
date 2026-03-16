import hashlib
import json
from datetime import datetime
from database import get_db


class Block:
    """Represents a single block in the blockchain."""
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'hash': self.hash,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }


class BlockchainService:
    """Mock blockchain service using SHA-256 hash chain."""

    def __init__(self):
        self.chain = []
        self._load_chain()

    def _load_chain(self):
        """Load chain from database or create genesis block."""
        db = get_db()
        blocks = db.execute(
            'SELECT * FROM blockchain_blocks ORDER BY block_index ASC'
        ).fetchall()
        db.close()

        if not blocks:
            self._create_genesis_block()
        else:
            for block_row in blocks:
                block = Block(
                    index=block_row['block_index'],
                    timestamp=block_row['timestamp'],
                    data=json.loads(block_row['data']),
                    previous_hash=block_row['previous_hash'],
                    nonce=block_row['nonce']
                )
                block.hash = block_row['data_hash']
                self.chain.append(block)

    def _create_genesis_block(self):
        """Create the first block in the chain."""
        genesis = Block(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            data={'event': 'genesis', 'message': 'TouristGuard 360 Blockchain Initialized'},
            previous_hash='0'
        )
        self.chain.append(genesis)
        self._save_block(genesis)

    def _save_block(self, block):
        """Persist block to database."""
        db = get_db()
        db.execute(
            '''INSERT INTO blockchain_blocks 
               (block_index, timestamp, data, data_hash, previous_hash, nonce) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (block.index, block.timestamp, json.dumps(block.data),
             block.hash, block.previous_hash, block.nonce)
        )
        db.commit()
        db.close()

    def add_block(self, data):
        """Add a new block to the chain."""
        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        self._save_block(new_block)
        return new_block.to_dict()

    def get_chain(self):
        """Return the full chain."""
        return [block.to_dict() for block in self.chain]

    def verify_chain(self):
        """Verify the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verify current block hash
            if current.hash != current.calculate_hash():
                return {
                    'valid': False,
                    'error': f'Block {i} hash is invalid',
                    'block_index': i
                }

            # Verify chain link
            if current.previous_hash != previous.hash:
                return {
                    'valid': False,
                    'error': f'Block {i} previous hash does not match block {i-1}',
                    'block_index': i
                }

        return {
            'valid': True,
            'length': len(self.chain),
            'message': 'Blockchain integrity verified'
        }

    def record_event(self, event_type, user_id=None, details=None):
        """Record a security event on the blockchain."""
        data = {
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        return self.add_block(data)


# Singleton instance
blockchain = BlockchainService()
