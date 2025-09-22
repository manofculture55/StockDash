"""
Authentication Module for StockDash
Handles JWT tokens, password hashing, and user authentication
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database import get_user_by_username, get_user_by_email, get_user_by_id, create_user


# Configuration
import os
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())  # Auto-generate secure key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_jwt_token(user_id: int, username: str) -> str:
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}


def register_user(username: str, email: str, password: str, first_name: str = '', last_name: str = '') -> dict:
    """Register a new user"""
    
    # Validate input
    if len(username) < 3:
        return {'error': 'Username must be at least 3 characters'}
    
    if len(password) < 6:
        return {'error': 'Password must be at least 6 characters'}
    
    if '@' not in email:
        return {'error': 'Invalid email format'}
    
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return {'error': 'Username already exists'}
    
    existing_email = get_user_by_email(email)
    if existing_email:
        return {'error': 'Email already registered'}
    
    # Hash password and create user
    password_hash = hash_password(password)
    
    try:
        user_id = create_user(username, email, password_hash, first_name, last_name)
        token = generate_jwt_token(user_id, username)
        
        return {
            'success': True,
            'user_id': user_id,
            'username': username,
            'email': email,
            'token': token,
            'message': 'User registered successfully'
        }
    except Exception as e:
        return {'error': f'Registration failed: {str(e)}'}


def login_user(username: str, password: str) -> dict:
    """Authenticate user and return JWT token"""
    
    # Find user (try username first, then email)
    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)  # Allow login with email
    
    if not user:
        return {'error': 'User not found'}
    
    # Verify password
    if not verify_password(password, user['password_hash']):
        return {'error': 'Invalid password'}
    
    # Generate token
    token = generate_jwt_token(user['id'], user['username'])
    
    return {
        'success': True,
        'user_id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'first_name': user.get('first_name', ''),
        'last_name': user.get('last_name', ''),
        'token': token,
        'message': 'Login successful'
    }


def jwt_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Decode token
        payload = decode_jwt_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401
        
        # Add user info to request context
        request.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username']
        }
        
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Get current authenticated user from request context"""
    return getattr(request, 'current_user', None)


# Test function
def test_auth():
    """Test authentication functions"""
    print("🧪 Testing authentication module...")
    
    # Test password hashing
    password = "test123"
    hashed = hash_password(password)
    print(f"✅ Password hashed: {hashed[:20]}...")
    
    # Test password verification
    is_valid = verify_password(password, hashed)
    print(f"✅ Password verification: {is_valid}")
    
    # Test token generation
    token = generate_jwt_token(1, "testuser")
    print(f"✅ JWT token generated: {token[:20]}...")
    
    # Test token decoding
    decoded = decode_jwt_token(token)
    print(f"✅ Token decoded: user_id={decoded.get('user_id')}")
    
    print("🎉 Authentication module tests passed!")


if __name__ == '__main__':
    test_auth()
