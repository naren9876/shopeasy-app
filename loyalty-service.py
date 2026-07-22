#!/usr/bin/env python3
"""
Loyalty Service Microservice
Manages customer loyalty points and rewards
"""

from flask import Flask, jsonify, request
from datetime import datetime
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Mock loyalty database
loyalty_db = {
    "user123": {
        "user_id": "user123",
        "points": 1500,
        "tier": "gold",
        "joined_at": "2023-01-01",
        "last_purchase": "2024-01-15",
        "total_spent": 5000.00
    }
}

# Reward tiers
TIER_THRESHOLDS = {
    'bronze': 0,
    'silver': 1000,
    'gold': 5000,
    'platinum': 10000
}

# Environment variables
SERVICE_NAME = os.getenv('SERVICE_NAME', 'loyalty-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
POINTS_MULTIPLIER = float(os.getenv('POINTS_MULTIPLIER', '1.0'))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return jsonify({
        'ready': True,
        'service': SERVICE_NAME
    }), 200

def calculate_tier(points):
    """Calculate loyalty tier based on points"""
    for tier in reversed(sorted(TIER_THRESHOLDS.keys(), 
                               key=lambda x: TIER_THRESHOLDS[x])):
        if points >= TIER_THRESHOLDS[tier]:
            return tier
    return 'bronze'

@app.route('/loyalty/<user_id>', methods=['GET'])
def get_loyalty(user_id):
    """Get loyalty information for user"""
    logger.info(f"[{SERVICE_NAME}] Fetching loyalty data for user: {user_id}")
    
    if user_id not in loyalty_db:
        # Create new loyalty account
        logger.info(f"[{SERVICE_NAME}] Creating new loyalty account for user: {user_id}")
        loyalty_db[user_id] = {
            'user_id': user_id,
            'points': 0,
            'tier': 'bronze',
            'joined_at': datetime.now().isoformat(),
            'last_purchase': None,
            'total_spent': 0.00
        }
    
    return jsonify({
        'service': SERVICE_NAME,
        'loyalty': loyalty_db[user_id],
        'tier_info': TIER_THRESHOLDS
    }), 200

@app.route('/loyalty/<user_id>/add-points', methods=['POST'])
def add_points(user_id):
    """Add loyalty points to user account"""
    data = request.get_json()
    points = data.get('points', 0)
    
    logger.info(f"[{SERVICE_NAME}] Adding {points} points to user: {user_id}")
    
    if user_id not in loyalty_db:
        loyalty_db[user_id] = {
            'user_id': user_id,
            'points': 0,
            'tier': 'bronze',
            'joined_at': datetime.now().isoformat(),
            'last_purchase': None,
            'total_spent': 0.00
        }
    
    # Apply points multiplier
    actual_points = int(points * POINTS_MULTIPLIER)
    
    loyalty_db[user_id]['points'] += actual_points
    loyalty_db[user_id]['tier'] = calculate_tier(loyalty_db[user_id]['points'])
    
    logger.info(f"[{SERVICE_NAME}] Points added. New total: {loyalty_db[user_id]['points']}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'user_id': user_id,
        'points_added': actual_points,
        'loyalty': loyalty_db[user_id],
        'message': f'{actual_points} points added successfully'
    }), 200

@app.route('/loyalty/<user_id>/redeem', methods=['POST'])
def redeem_points(user_id):
    """Redeem loyalty points"""
    data = request.get_json()
    points = data.get('points', 0)
    reward = data.get('reward', 'discount')
    
    logger.info(f"[{SERVICE_NAME}] Redeeming {points} points for user: {user_id}")
    
    if user_id not in loyalty_db:
        return jsonify({'error': 'User not found'}), 404
    
    if loyalty_db[user_id]['points'] < points:
        return jsonify({
            'error': 'Insufficient points',
            'available': loyalty_db[user_id]['points'],
            'requested': points
        }), 400
    
    loyalty_db[user_id]['points'] -= points
    loyalty_db[user_id]['tier'] = calculate_tier(loyalty_db[user_id]['points'])
    
    # Generate reward
    discount_amount = (points / 100) * 5  # 1 point = 0.05 discount
    
    logger.info(f"[{SERVICE_NAME}] Points redeemed. New total: {loyalty_db[user_id]['points']}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'user_id': user_id,
        'points_redeemed': points,
        'reward_type': reward,
        'discount_amount': discount_amount,
        'loyalty': loyalty_db[user_id],
        'message': f'{points} points redeemed successfully'
    }), 200

@app.route('/loyalty/<user_id>/purchase', methods=['POST'])
def record_purchase(user_id):
    """Record a purchase and add points"""
    data = request.get_json()
    amount = data.get('amount', 0)
    
    logger.info(f"[{SERVICE_NAME}] Recording purchase for user: {user_id}, Amount: ${amount}")
    
    if user_id not in loyalty_db:
        loyalty_db[user_id] = {
            'user_id': user_id,
            'points': 0,
            'tier': 'bronze',
            'joined_at': datetime.now().isoformat(),
            'last_purchase': None,
            'total_spent': 0.00
        }
    
    # Calculate points: 1 point per dollar spent
    points = int(amount)
    
    loyalty_db[user_id]['points'] += points
    loyalty_db[user_id]['total_spent'] += amount
    loyalty_db[user_id]['last_purchase'] = datetime.now().isoformat()
    loyalty_db[user_id]['tier'] = calculate_tier(loyalty_db[user_id]['points'])
    
    logger.info(f"[{SERVICE_NAME}] Purchase recorded. Points added: {points}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'user_id': user_id,
        'purchase_amount': amount,
        'points_earned': points,
        'loyalty': loyalty_db[user_id],
        'message': f'Purchase recorded and {points} points earned'
    }), 201

@app.route('/loyalty/rewards', methods=['GET'])
def get_rewards_catalog():
    """Get available rewards"""
    logger.info(f"[{SERVICE_NAME}] Fetching rewards catalog")
    
    rewards = [
        {
            'id': 'reward_001',
            'name': '10% Discount',
            'points_required': 100,
            'value': 10.0
        },
        {
            'id': 'reward_002',
            'name': 'Free Shipping',
            'points_required': 50,
            'value': 'free_shipping'
        },
        {
            'id': 'reward_003',
            'name': '$20 Gift Card',
            'points_required': 500,
            'value': 20.0
        },
        {
            'id': 'reward_004',
            'name': 'Birthday Bonus',
            'points_required': 200,
            'value': 'birthday_bonus'
        }
    ]
    
    return jsonify({
        'service': SERVICE_NAME,
        'rewards': rewards,
        'count': len(rewards)
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint"""
    total_points = sum(u['points'] for u in loyalty_db.values())
    total_spent = sum(u['total_spent'] for u in loyalty_db.values())
    
    return jsonify({
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'environment': ENVIRONMENT,
        'total_users': len(loyalty_db),
        'total_points_issued': total_points,
        'total_spent': total_spent,
        'points_multiplier': POINTS_MULTIPLIER
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    debug = ENVIRONMENT == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
