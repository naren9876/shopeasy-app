#!/usr/bin/env python3
"""
Account Service Microservice
Handles user registration, login, and profile management
"""

from flask import Flask, jsonify, request
from datetime import datetime
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Mock database (in production, use real database)
users_db = {
    "user123": {
        "id": "user123",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "created_at": "2024-01-01"
    }
}

# Environment variables
SERVICE_NAME = os.getenv('SERVICE_NAME', 'account-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'deployed_by': 'pipeline',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return jsonify({
        'ready': True,
        'service': SERVICE_NAME
    }), 200

@app.route('/users', methods=['GET'])
def list_users():
    """List all users"""
    logger.info(f"[{SERVICE_NAME}] Fetching users list")
    return jsonify({
        'service': SERVICE_NAME,
        'environment': ENVIRONMENT,
        'users': list(users_db.values())
    }), 200

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    logger.info(f"[{SERVICE_NAME}] Fetching user: {user_id}")
    
    if user_id not in users_db:
        return jsonify({
            'error': 'User not found',
            'user_id': user_id
        }), 404
    
    return jsonify({
        'service': SERVICE_NAME,
        'user': users_db[user_id]
    }), 200

@app.route('/users', methods=['POST'])
def create_user():
    """Create new user"""
    data = request.get_json()
    logger.info(f"[{SERVICE_NAME}] Creating new user: {data.get('email')}")
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    user_id = data.get('email', '').replace('@', '_').replace('.', '_')
    
    if user_id in users_db:
        return jsonify({'error': 'User already exists'}), 409
    
    new_user = {
        'id': user_id,
        'name': data.get('name', 'Unknown'),
        'email': data.get('email'),
        'phone': data.get('phone', ''),
        'created_at': datetime.now().isoformat()
    }
    
    users_db[user_id] = new_user
    logger.info(f"[{SERVICE_NAME}] User created: {user_id}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'user': new_user,
        'message': 'User created successfully'
    }), 201

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    logger.info(f"[{SERVICE_NAME}] Updating user: {user_id}")
    
    if user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    users_db[user_id].update(data)
    
    logger.info(f"[{SERVICE_NAME}] User updated: {user_id}")
    return jsonify({
        'service': SERVICE_NAME,
        'user': users_db[user_id],
        'message': 'User updated successfully'
    }), 200

@app.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    email = data.get('email')
    
    logger.info(f"[{SERVICE_NAME}] Login attempt: {email}")
    
    # Simple validation (in production, use real authentication)
    user_id = email.replace('@', '_').replace('.', '_')
    
    if user_id not in users_db:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({
        'service': SERVICE_NAME,
        'token': f"jwt_token_{user_id}",
        'user_id': user_id,
        'message': 'Login successful'
    }), 200

@app.route('/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    logger.info(f"[{SERVICE_NAME}] User logged out")
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Simple metrics endpoint"""
    return jsonify({
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'total_users': len(users_db),
        'environment': ENVIRONMENT
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = ENVIRONMENT == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
