# -*- coding: utf-8 -*-
"""Shared configuration and environment variables"""
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback_secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# AI Config
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Viva Payments Config
VIVA_CLIENT_ID = os.environ.get('VIVA_CLIENT_ID', '')
VIVA_CLIENT_SECRET = os.environ.get('VIVA_CLIENT_SECRET', '')
VIVA_API_URL = os.environ.get('VIVA_API_URL', 'https://api.vivapayments.com')
VIVA_CHECKOUT_URL = 'https://www.vivapayments.com/web/checkout'
VIVA_SOURCE_CODE = os.environ.get('VIVA_SOURCE_CODE', '9806')
VIVA_WEBHOOK_KEY = os.environ.get('VIVA_WEBHOOK_KEY', '475FFE73819D67134BBB2D6690A9023714C14E2E')

# Resend Email Config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# VAPID Push Notification Config
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '').replace('\\n', '\n')
VAPID_MAILTO = os.environ.get('VAPID_MAILTO', 'mailto:support@zektrix.uk')

# Write VAPID PEM file from env variable
vapid_pem_path = os.path.join(os.path.dirname(__file__), "vapid_private.pem")
if VAPID_PRIVATE_KEY and VAPID_PRIVATE_KEY.startswith('-----BEGIN'):
    with open(vapid_pem_path, 'w') as f:
        f.write(VAPID_PRIVATE_KEY.strip() + '\n')

# Derive VAPID public key from private key
VAPID_PUBLIC_KEY = ''
if os.path.exists(vapid_pem_path):
    try:
        from cryptography.hazmat.primitives import serialization as _ser
        with open(vapid_pem_path, 'rb') as f:
            _pk = _ser.load_pem_private_key(f.read(), password=None)
        VAPID_PUBLIC_KEY = base64.urlsafe_b64encode(
            _pk.public_key().public_bytes(_ser.Encoding.X962, _ser.PublicFormat.UncompressedPoint)
        ).rstrip(b'=').decode()
    except Exception as e:
        logger.error(f"Failed to derive VAPID public key: {e}")
        VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Resend setup
if RESEND_API_KEY:
    import resend
    resend.api_key = RESEND_API_KEY
