#!/usr/bin/env python3
"""
Payment Service Microservice
Handles payment processing and transactions
"""

from flask import Flask, jsonify, request
from datetime import datetime
import os
import logging
import uuid

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Mock transaction database
transactions_db = {
    "txn_001": {
        "transaction_id": "txn_001",
        "user_id": "user123",
        "amount": 99.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "credit_card",
        "created_at": "2024-01-15"
    }
}

# Environment variables
SERVICE_NAME = os.getenv('SERVICE_NAME', 'payment-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
PAYMENT_GATEWAY = os.getenv('PAYMENT_GATEWAY', 'stripe')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'gateway': PAYMENT_GATEWAY,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return jsonify({
        'ready': True,
        'service': SERVICE_NAME
    }), 200

@app.route('/payments', methods=['GET'])
def list_payments():
    """List all transactions"""
    logger.info(f"[{SERVICE_NAME}] Fetching transactions list")
    
    user_id = request.args.get('user_id')
    
    if user_id:
        filtered = {k: v for k, v in transactions_db.items() 
                   if v['user_id'] == user_id}
        return jsonify({
            'service': SERVICE_NAME,
            'user_id': user_id,
            'transactions': list(filtered.values()),
            'count': len(filtered)
        }), 200
    
    return jsonify({
        'service': SERVICE_NAME,
        'transactions': list(transactions_db.values()),
        'count': len(transactions_db)
    }), 200

@app.route('/payments/<transaction_id>', methods=['GET'])
def get_payment(transaction_id):
    """Get specific transaction"""
    logger.info(f"[{SERVICE_NAME}] Fetching transaction: {transaction_id}")
    
    if transaction_id not in transactions_db:
        return jsonify({
            'error': 'Transaction not found',
            'transaction_id': transaction_id
        }), 404
    
    return jsonify({
        'service': SERVICE_NAME,
        'transaction': transactions_db[transaction_id]
    }), 200

@app.route('/payments/process', methods=['POST'])
def process_payment():
    """Process a payment"""
    data = request.get_json()
    logger.info(f"[{SERVICE_NAME}] Processing payment for user: {data.get('user_id')}")
    
    # Validate required fields
    required_fields = ['user_id', 'amount', 'currency', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({
            'error': f'Missing required fields: {required_fields}'
        }), 400
    
    # Create transaction
    transaction_id = f"txn_{str(uuid.uuid4())[:8]}"
    
    transaction = {
        'transaction_id': transaction_id,
        'user_id': data['user_id'],
        'amount': data['amount'],
        'currency': data['currency'],
        'payment_method': data['payment_method'],
        'status': 'pending',
        'gateway': PAYMENT_GATEWAY,
        'created_at': datetime.now().isoformat()
    }
    
    # Simulate payment processing
    logger.info(f"[{SERVICE_NAME}] Processing with gateway: {PAYMENT_GATEWAY}")
    
    # In production, call actual payment gateway (Stripe, PayPal, etc.)
    transaction['status'] = 'completed'  # Simulated success
    
    transactions_db[transaction_id] = transaction
    
    logger.info(f"[{SERVICE_NAME}] Payment processed: {transaction_id}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'transaction': transaction,
        'message': 'Payment processed successfully'
    }), 201

@app.route('/payments/<transaction_id>/refund', methods=['POST'])
def refund_payment(transaction_id):
    """Refund a payment"""
    logger.info(f"[{SERVICE_NAME}] Refunding transaction: {transaction_id}")
    
    if transaction_id not in transactions_db:
        return jsonify({
            'error': 'Transaction not found',
            'transaction_id': transaction_id
        }), 404
    
    transaction = transactions_db[transaction_id]
    transaction['status'] = 'refunded'
    transaction['refunded_at'] = datetime.now().isoformat()
    
    logger.info(f"[{SERVICE_NAME}] Transaction refunded: {transaction_id}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'transaction': transaction,
        'message': 'Payment refunded successfully'
    }), 200

@app.route('/validate-payment-method', methods=['POST'])
def validate_payment_method():
    """Validate payment method"""
    data = request.get_json()
    logger.info(f"[{SERVICE_NAME}] Validating payment method")
    
    # Simple validation (in production, use real validation)
    is_valid = True
    
    return jsonify({
        'service': SERVICE_NAME,
        'valid': is_valid,
        'payment_method': data.get('payment_method')
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint"""
    completed = sum(1 for t in transactions_db.values() if t['status'] == 'completed')
    total_amount = sum(t['amount'] for t in transactions_db.values() if t['status'] == 'completed')
    
    return jsonify({
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'environment': ENVIRONMENT,
        'payment_gateway': PAYMENT_GATEWAY,
        'total_transactions': len(transactions_db),
        'completed_transactions': completed,
        'total_amount_processed': total_amount
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = ENVIRONMENT == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
