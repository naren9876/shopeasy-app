# Retail Microservices - API Testing Examples

Complete curl command examples for testing the retail microservices.
Run with Docker Compose or local deployment.

---

## Setup

Make sure all services are running:
```bash
docker-compose up -d
# or run each service in separate terminals
```

Base URLs:
- Account Service: `http://localhost:5000`
- Payment Service: `http://localhost:5001`
- Loyalty Service: `http://localhost:5002`
- Checkout Service: `http://localhost:5003`

---

## SCENARIO 1: New Customer Registration & Purchase

### 1.1 Create New Customer Account

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "phone": "+1-555-0001"
  }'

# Expected Response:
# {
#   "service": "account-service",
#   "user": {
#     "id": "sarah_johnson@example_com",
#     "name": "Sarah Johnson",
#     "email": "sarah.johnson@example.com",
#     "phone": "+1-555-0001",
#     "created_at": "2024-01-20T10:30:45.123456"
#   },
#   "message": "User created successfully"
# }
```

### 1.2 User Login

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sarah.johnson@example.com"
  }'

# Expected Response:
# {
#   "service": "account-service",
#   "token": "jwt_token_sarah_johnson@example_com",
#   "user_id": "sarah_johnson@example_com",
#   "message": "Login successful"
# }
```

### 1.3 Check Loyalty Account (Auto-created)

```bash
curl http://localhost:5002/loyalty/sarah_johnson@example_com

# Expected Response:
# {
#   "service": "loyalty-service",
#   "loyalty": {
#     "user_id": "sarah_johnson@example_com",
#     "points": 0,
#     "tier": "bronze",
#     "joined_at": "2024-01-20T10:35:22.654321",
#     "last_purchase": null,
#     "total_spent": 0.00
#   },
#   "tier_info": {
#     "bronze": 0,
#     "silver": 1000,
#     "gold": 5000,
#     "platinum": 10000
#   }
# }
```

---

## SCENARIO 2: Shopping Cart & Checkout

### 2.1 View Empty Cart

```bash
curl http://localhost:5003/cart/sarah_johnson@example_com

# Expected Response:
# {
#   "service": "checkout-service",
#   "cart": {
#     "user_id": "sarah_johnson@example_com",
#     "items": [],
#     "subtotal": 0,
#     "tax": 0,
#     "total": 0,
#     "created_at": "2024-01-20T10:36:00.000000"
#   }
# }
```

### 2.2 Add Products to Cart

```bash
# Add Laptop
curl -X POST http://localhost:5003/cart/sarah_johnson@example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_laptop_001",
    "name": "MacBook Pro 14\"",
    "price": 1999.99,
    "quantity": 1
  }'

# Add Mouse
curl -X POST http://localhost:5003/cart/sarah_johnson@example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_mouse_001",
    "name": "Wireless Magic Mouse",
    "price": 79.99,
    "quantity": 1
  }'

# Add USB-C Cable
curl -X POST http://localhost:5003/cart/sarah_johnson@example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_cable_001",
    "name": "USB-C Thunderbolt 3 Cable",
    "price": 29.99,
    "quantity": 2
  }'

# Expected Response for each:
# {
#   "service": "checkout-service",
#   "cart": {
#     "user_id": "sarah_johnson@example_com",
#     "items": [...],
#     "subtotal": 2139.96,
#     "tax": 171.20,
#     "total": 2311.16
#   },
#   "message": "Item added to cart"
# }
```

### 2.3 View Cart with Items

```bash
curl http://localhost:5003/cart/sarah_johnson@example_com

# Expected Response:
# {
#   "service": "checkout-service",
#   "cart": {
#     "user_id": "sarah_johnson@example_com",
#     "items": [
#       {
#         "product_id": "prod_laptop_001",
#         "name": "MacBook Pro 14\"",
#         "price": 1999.99,
#         "quantity": 1
#       },
#       {
#         "product_id": "prod_mouse_001",
#         "name": "Wireless Magic Mouse",
#         "price": 79.99,
#         "quantity": 1
#       },
#       {
#         "product_id": "prod_cable_001",
#         "name": "USB-C Thunderbolt 3 Cable",
#         "price": 29.99,
#         "quantity": 2
#       }
#     ],
#     "subtotal": 2139.96,
#     "tax": 171.20,
#     "total": 2311.16
#   }
# }
```

### 2.4 Checkout

```bash
curl -X POST http://localhost:5003/checkout/sarah_johnson@example_com \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Apple Park Way",
      "city": "Cupertino",
      "state": "CA",
      "zip": "95014",
      "country": "USA"
    }
  }'

# Expected Response:
# {
#   "service": "checkout-service",
#   "order": {
#     "order_id": "order_a1b2c3d4",
#     "user_id": "sarah_johnson@example_com",
#     "items": [...],
#     "subtotal": 2139.96,
#     "tax": 171.20,
#     "total": 2311.16,
#     "status": "pending",
#     "shipping_address": {...},
#     "created_at": "2024-01-20T10:45:30.000000"
#   },
#   "message": "Order created successfully. Awaiting payment."
# }
```

---

## SCENARIO 3: Payment Processing

### 3.1 Process Payment

```bash
curl -X POST http://localhost:5001/payments/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "sarah_johnson@example_com",
    "amount": 2311.16,
    "currency": "USD",
    "payment_method": "credit_card"
  }'

# Expected Response:
# {
#   "service": "payment-service",
#   "transaction": {
#     "transaction_id": "txn_e5f6g7h8",
#     "user_id": "sarah_johnson@example_com",
#     "amount": 2311.16,
#     "currency": "USD",
#     "payment_method": "credit_card",
#     "status": "completed",
#     "gateway": "stripe",
#     "created_at": "2024-01-20T10:46:15.000000"
#   },
#   "message": "Payment processed successfully"
# }
```

### 3.2 View Transaction

```bash
curl http://localhost:5001/payments/txn_e5f6g7h8
```

### 3.3 List All Transactions for User

```bash
curl "http://localhost:5001/payments?user_id=sarah_johnson@example_com"
```

---

## SCENARIO 4: Loyalty Points & Rewards

### 4.1 Record Purchase (Auto-add Points)

```bash
curl -X POST http://localhost:5002/loyalty/sarah_johnson@example_com/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2311.16
  }'

# Expected Response:
# {
#   "service": "loyalty-service",
#   "user_id": "sarah_johnson@example_com",
#   "purchase_amount": 2311.16,
#   "points_earned": 2311,
#   "loyalty": {
#     "user_id": "sarah_johnson@example_com",
#     "points": 2311,
#     "tier": "silver",
#     "joined_at": "2024-01-20T10:35:22.654321",
#     "last_purchase": "2024-01-20T10:47:00.000000",
#     "total_spent": 2311.16
#   },
#   "message": "Purchase recorded and 2311 points earned"
# }
```

### 4.2 View Updated Loyalty Status

```bash
curl http://localhost:5002/loyalty/sarah_johnson@example_com

# Notice: tier changed from "bronze" to "silver" (1000+ points)
```

### 4.3 View Available Rewards

```bash
curl http://localhost:5002/loyalty/rewards

# Expected Response:
# {
#   "service": "loyalty-service",
#   "rewards": [
#     {
#       "id": "reward_001",
#       "name": "10% Discount",
#       "points_required": 100,
#       "value": 10.0
#     },
#     {
#       "id": "reward_002",
#       "name": "Free Shipping",
#       "points_required": 50,
#       "value": "free_shipping"
#     },
#     {
#       "id": "reward_003",
#       "name": "$20 Gift Card",
#       "points_required": 500,
#       "value": 20.0
#     },
#     {
#       "id": "reward_004",
#       "name": "Birthday Bonus",
#       "points_required": 200,
#       "value": "birthday_bonus"
#     }
#   ],
#   "count": 4
# }
```

### 4.4 Redeem Points for Reward

```bash
curl -X POST http://localhost:5002/loyalty/sarah_johnson@example_com/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "points": 500,
    "reward": "gift_card"
  }'

# Expected Response:
# {
#   "service": "loyalty-service",
#   "user_id": "sarah_johnson@example_com",
#   "points_redeemed": 500,
#   "reward_type": "gift_card",
#   "discount_amount": 25.00,
#   "loyalty": {
#     "user_id": "sarah_johnson@example_com",
#     "points": 1811,
#     "tier": "silver",
#     ...
#   },
#   "message": "500 points redeemed successfully"
# }
```

### 4.5 Manually Add Bonus Points

```bash
curl -X POST http://localhost:5002/loyalty/sarah_johnson@example_com/add-points \
  -H "Content-Type: application/json" \
  -d '{
    "points": 500
  }'

# Response shows updated points: 1811 + 500 = 2311
```

---

## SCENARIO 5: Repeat Customer (Existing Account)

### 5.1 Get Existing User

```bash
curl http://localhost:5000/users/sarah_johnson@example_com

# Expected Response:
# {
#   "service": "account-service",
#   "user": {
#     "id": "sarah_johnson@example_com",
#     "name": "Sarah Johnson",
#     "email": "sarah.johnson@example.com",
#     "phone": "+1-555-0001",
#     "created_at": "2024-01-20T10:30:45.123456"
#   }
# }
```

### 5.2 Update User Profile

```bash
curl -X PUT http://localhost:5000/users/sarah_johnson@example_com \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1-555-0002",
    "name": "Sarah J. Johnson"
  }'
```

### 5.3 Quick Loyalty Check

```bash
curl http://localhost:5002/loyalty/sarah_johnson@example_com

# Shows: 2311 points, silver tier, total spent: $2311.16
```

### 5.4 Make Another Purchase

```bash
# Add new item to cart
curl -X POST http://localhost:5003/cart/sarah_johnson@example_com/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_headphones_001",
    "name": "AirPods Pro",
    "price": 249.99,
    "quantity": 1
  }'

# Checkout
curl -X POST http://localhost:5003/checkout/sarah_johnson@example_com \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Apple Park Way",
      "city": "Cupertino",
      "state": "CA",
      "zip": "95014"
    }
  }'

# Process payment
curl -X POST http://localhost:5001/payments/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "sarah_johnson@example_com",
    "amount": 199.99,
    "currency": "USD",
    "payment_method": "credit_card"
  }'

# Record purchase and earn points
curl -X POST http://localhost:5002/loyalty/sarah_johnson@example_com/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 199.99
  }'

# New loyalty status: 2311 + 200 = 2511 points (still silver, needs 5000 for gold)
```

---

## SERVICE HEALTH & METRICS

### Check Service Health

```bash
# Account Service
curl http://localhost:5000/health

# Payment Service
curl http://localhost:5001/health

# Loyalty Service
curl http://localhost:5002/health

# Checkout Service
curl http://localhost:5003/health

# All should return similar response:
# {
#   "status": "healthy",
#   "service": "account-service",
#   "version": "1.0.0",
#   "timestamp": "2024-01-20T10:50:00.000000"
# }
```

### Check Service Readiness

```bash
curl http://localhost:5000/ready
curl http://localhost:5001/ready
curl http://localhost:5002/ready
curl http://localhost:5003/ready
```

### View Service Metrics

```bash
# Account Service metrics
curl http://localhost:5000/metrics
# {
#   "service": "account-service",
#   "version": "1.0.0",
#   "total_users": 1,
#   "environment": "development"
# }

# Payment Service metrics
curl http://localhost:5001/metrics
# {
#   "service": "payment-service",
#   "total_transactions": 2,
#   "completed_transactions": 2,
#   "total_amount_processed": 2511.15
# }

# Loyalty Service metrics
curl http://localhost:5002/metrics
# {
#   "service": "loyalty-service",
#   "total_users": 1,
#   "total_points_issued": 2511,
#   "total_spent": 2511.15
# }

# Checkout Service metrics
curl http://localhost:5003/metrics
# {
#   "service": "checkout-service",
#   "total_orders": 2,
#   "completed_orders": 0,
#   "total_sales": 0,
#   "active_carts": 1
# }
```

---

## Error Handling Examples

### Invalid Data

```bash
# Missing required field
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'

# Response:
# {
#   "error": "Email is required"
# }
```

### User Not Found

```bash
curl http://localhost:5000/users/nonexistent_user

# Response:
# {
#   "error": "User not found",
#   "user_id": "nonexistent_user"
# }
```

### Insufficient Loyalty Points

```bash
curl -X POST http://localhost:5002/loyalty/sarah_johnson@example_com/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "points": 999999,
    "reward": "luxury_item"
  }'

# Response:
# {
#   "error": "Insufficient points",
#   "available": 2511,
#   "requested": 999999
# }
```

---

## Batch Operations (Advanced)

### Create Multiple Users

```bash
for i in {1..5}; do
  curl -X POST http://localhost:5000/users \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"User $i\",
      \"email\": \"user$i@example.com\",
      \"phone\": \"+1-555-000$i\"
    }"
  echo ""
done
```

### Simulate Multiple Purchases

```bash
# Create 3 users with purchases
users=("user1_example_com" "user2_example_com" "user3_example_com")

for user in "${users[@]}"; do
  # Process payment
  curl -X POST http://localhost:5001/payments/process \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$user\",
      \"amount\": $((RANDOM % 500 + 50)),
      \"currency\": \"USD\",
      \"payment_method\": \"credit_card\"
    }"
  echo ""
done
```

---

## Tips for Testing

1. **Save user IDs**: Use user IDs from create responses for subsequent calls
2. **Check dependencies**: User must exist before creating loyalty/orders
3. **Order matters**: Create account → Login → Add to cart → Checkout → Pay → Earn points
4. **Use jq for formatting**: `curl ... | jq '.'` for pretty JSON output
5. **Save to files**: `curl ... > response.json`
6. **Use postman**: Import these as Postman collection for GUI testing

---

Good luck testing! 🚀
