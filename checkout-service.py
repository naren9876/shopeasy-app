#!/usr/bin/env python3
"""
Checkout Service Microservice
Handles shopping cart and order processing
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

# Mock databases
carts_db = {
    "user123": {
        "user_id": "user123",
        "items": [
            {
                "product_id": "prod_001",
                "name": "Laptop",
                "price": 999.99,
                "quantity": 1
            }
        ],
        "subtotal": 999.99,
        "tax": 79.99,
        "total": 1079.98,
        "created_at": "2024-01-15"
    }
}

orders_db = {
    "order_001": {
        "order_id": "order_001",
        "user_id": "user123",
        "items": [
            {
                "product_id": "prod_001",
                "name": "Laptop",
                "price": 999.99,
                "quantity": 1
            }
        ],
        "subtotal": 999.99,
        "tax": 79.99,
        "total": 1079.98,
        "status": "completed",
        "created_at": "2024-01-01"
    }
}

# Environment variables
SERVICE_NAME = os.getenv('SERVICE_NAME', 'checkout-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
TAX_RATE = float(os.getenv('TAX_RATE', '0.08'))

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

def calculate_totals(items):
    """Calculate subtotal, tax, and total"""
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax, 2)
    return subtotal, tax, total

@app.route('/cart/<user_id>', methods=['GET'])
def get_cart(user_id):
    """Get user's shopping cart"""
    logger.info(f"[{SERVICE_NAME}] Fetching cart for user: {user_id}")
    
    if user_id not in carts_db:
        # Create empty cart
        carts_db[user_id] = {
            'user_id': user_id,
            'items': [],
            'subtotal': 0,
            'tax': 0,
            'total': 0,
            'created_at': datetime.now().isoformat()
        }
    
    return jsonify({
        'service': SERVICE_NAME,
        'cart': carts_db[user_id]
    }), 200

@app.route('/cart/<user_id>/add-item', methods=['POST'])
def add_to_cart(user_id):
    """Add item to cart"""
    data = request.get_json()
    logger.info(f"[{SERVICE_NAME}] Adding item to cart for user: {user_id}")
    
    if user_id not in carts_db:
        carts_db[user_id] = {
            'user_id': user_id,
            'items': [],
            'subtotal': 0,
            'tax': 0,
            'total': 0,
            'created_at': datetime.now().isoformat()
        }
    
    # Validate item data
    required_fields = ['product_id', 'name', 'price', 'quantity']
    if not all(field in data for field in required_fields):
        return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
    
    # Check if item already in cart
    item_exists = False
    for item in carts_db[user_id]['items']:
        if item['product_id'] == data['product_id']:
            item['quantity'] += data['quantity']
            item_exists = True
            break
    
    if not item_exists:
        carts_db[user_id]['items'].append({
            'product_id': data['product_id'],
            'name': data['name'],
            'price': data['price'],
            'quantity': data['quantity']
        })
    
    # Recalculate totals
    subtotal, tax, total = calculate_totals(carts_db[user_id]['items'])
    carts_db[user_id]['subtotal'] = subtotal
    carts_db[user_id]['tax'] = tax
    carts_db[user_id]['total'] = total
    
    logger.info(f"[{SERVICE_NAME}] Item added to cart. New total: ${total}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'cart': carts_db[user_id],
        'message': 'Item added to cart'
    }), 201

@app.route('/cart/<user_id>/remove-item', methods=['POST'])
def remove_from_cart(user_id):
    """Remove item from cart"""
    data = request.get_json()
    product_id = data.get('product_id')
    
    logger.info(f"[{SERVICE_NAME}] Removing item from cart for user: {user_id}")
    
    if user_id not in carts_db:
        return jsonify({'error': 'Cart not found'}), 404
    
    # Remove item
    carts_db[user_id]['items'] = [
        item for item in carts_db[user_id]['items'] 
        if item['product_id'] != product_id
    ]
    
    # Recalculate totals
    subtotal, tax, total = calculate_totals(carts_db[user_id]['items'])
    carts_db[user_id]['subtotal'] = subtotal
    carts_db[user_id]['tax'] = tax
    carts_db[user_id]['total'] = total
    
    logger.info(f"[{SERVICE_NAME}] Item removed from cart. New total: ${total}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'cart': carts_db[user_id],
        'message': 'Item removed from cart'
    }), 200

@app.route('/cart/<user_id>/clear', methods=['POST'])
def clear_cart(user_id):
    """Clear entire cart"""
    logger.info(f"[{SERVICE_NAME}] Clearing cart for user: {user_id}")
    
    if user_id not in carts_db:
        return jsonify({'error': 'Cart not found'}), 404
    
    carts_db[user_id]['items'] = []
    carts_db[user_id]['subtotal'] = 0
    carts_db[user_id]['tax'] = 0
    carts_db[user_id]['total'] = 0
    
    return jsonify({
        'service': SERVICE_NAME,
        'message': 'Cart cleared'
    }), 200

@app.route('/checkout/<user_id>', methods=['POST'])
def checkout(user_id):
    """Process checkout and create order"""
    logger.info(f"[{SERVICE_NAME}] Processing checkout for user: {user_id}")
    
    if user_id not in carts_db:
        return jsonify({'error': 'Cart not found'}), 404
    
    cart = carts_db[user_id]
    
    if not cart['items']:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Create order
    order_id = f"order_{str(uuid.uuid4())[:8]}"
    
    order = {
        'order_id': order_id,
        'user_id': user_id,
        'items': cart['items'].copy(),
        'subtotal': cart['subtotal'],
        'tax': cart['tax'],
        'total': cart['total'],
        'status': 'pending',
        'shipping_address': None,
        'created_at': datetime.now().isoformat()
    }
    
    # Validate shipping address
    data = request.get_json() or {}
    if data.get('shipping_address'):
        order['shipping_address'] = data['shipping_address']
    else:
        return jsonify({'error': 'Shipping address is required'}), 400
    
    orders_db[order_id] = order
    
    # Clear cart after successful checkout
    carts_db[user_id]['items'] = []
    carts_db[user_id]['subtotal'] = 0
    carts_db[user_id]['tax'] = 0
    carts_db[user_id]['total'] = 0
    
    logger.info(f"[{SERVICE_NAME}] Order created: {order_id}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'order': order,
        'message': 'Order created successfully. Awaiting payment.'
    }), 201

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    logger.info(f"[{SERVICE_NAME}] Fetching order: {order_id}")
    
    if order_id not in orders_db:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'service': SERVICE_NAME,
        'order': orders_db[order_id]
    }), 200

@app.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order"""
    logger.info(f"[{SERVICE_NAME}] Cancelling order: {order_id}")
    
    if order_id not in orders_db:
        return jsonify({'error': 'Order not found'}), 404
    
    order = orders_db[order_id]
    
    if order['status'] == 'completed':
        return jsonify({'error': 'Cannot cancel completed order'}), 400
    
    order['status'] = 'cancelled'
    order['cancelled_at'] = datetime.now().isoformat()
    
    logger.info(f"[{SERVICE_NAME}] Order cancelled: {order_id}")
    
    return jsonify({
        'service': SERVICE_NAME,
        'order': order,
        'message': 'Order cancelled successfully'
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint"""
    total_orders = len(orders_db)
    completed = sum(1 for o in orders_db.values() if o['status'] == 'completed')
    total_sales = sum(o['total'] for o in orders_db.values() if o['status'] == 'completed')
    
    return jsonify({
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'environment': ENVIRONMENT,
        'tax_rate': TAX_RATE,
        'total_orders': total_orders,
        'completed_orders': completed,
        'total_sales': total_sales,
        'active_carts': len(carts_db)
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5003))
    debug = ENVIRONMENT == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
