"""
Fyers OAuth Authentication Handler.
Manages access token generation and validation.

IMPORTANT: Fyers access tokens expire at midnight every day (IST).
This module handles token validation and provides helpers for re-authentication.

TOTP Auto-Login: If FYERS_TOTP_SECRET and FYERS_PIN are configured,
the system can automatically generate new tokens without manual login.
"""
import os
import jwt
import webbrowser
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from pathlib import Path
from loguru import logger

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logger.warning("⚠️ pyotp not installed. TOTP auto-login disabled. Install with: pip install pyotp")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from config import get_config

config = get_config()


class FyersAuthManager:
    """
    Manages Fyers OAuth authentication.

    Token Flow (Manual):
    1. Generate auth URL (user visits in browser)
    2. User logs in and gets auth_code from redirect
    3. Exchange auth_code for access_token
    4. Access token valid until midnight IST

    Token Flow (TOTP Auto-Login):
    1. Generate TOTP from secret
    2. Automated login via Fyers API
    3. Get auth_code automatically
    4. Exchange for access_token
    """

    def __init__(self):
        self.app_id = config.FYERS_APP_ID
        self.secret_key = config.FYERS_SECRET_KEY
        self.redirect_uri = config.FYERS_REDIRECT_URI
        self.totp_secret = getattr(config, 'FYERS_TOTP_SECRET', None)
        self.pin = getattr(config, 'FYERS_PIN', None)
        self.token_file = Path(__file__).parent.parent / "data" / "fyers_token.txt"

        # Ensure data directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if TOTP auto-login is available
        self.totp_enabled = (
            PYOTP_AVAILABLE and
            self.totp_secret and
            self.pin and
            len(self.totp_secret) > 0 and
            len(self.pin) > 0
        )
        if self.totp_enabled:
            logger.info("✅ TOTP auto-login is configured")
        else:
            logger.info("ℹ️ TOTP auto-login not configured - manual login required")
    
    def is_token_valid(self, access_token: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check if the access token is valid.
        
        Returns:
            (is_valid, reason)
        """
        token = access_token or config.FYERS_ACCESS_TOKEN
        
        if not token:
            return False, "No access token configured"
        
        try:
            # Decode JWT without verification (just to check expiry)
            # Fyers tokens use HS256, we don't have their secret
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            exp_timestamp = decoded.get('exp')
            if not exp_timestamp:
                return False, "Token has no expiry claim"
            
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            
            # Check if expired
            if now >= exp_datetime:
                return False, f"Token expired at {exp_datetime}"
            
            # Check if expiring soon (within 1 hour)
            if now >= exp_datetime - timedelta(hours=1):
                logger.warning(f"⚠️ Token expiring soon at {exp_datetime}")
                return True, f"Token expiring soon at {exp_datetime}"
            
            # Get user ID from token
            fy_id = decoded.get('fy_id', 'Unknown')
            logger.info(f"✅ Token valid for {fy_id}, expires at {exp_datetime}")
            
            return True, f"Valid until {exp_datetime}"
            
        except jwt.DecodeError as e:
            return False, f"Invalid token format: {e}"
        except Exception as e:
            return False, f"Token validation error: {e}"
    
    def get_auth_url(self) -> str:
        """
        Generate the OAuth authorization URL.
        User must visit this URL to login and get auth_code.
        """
        base_url = "https://api-t1.fyers.in/api/v3/generate-authcode"
        
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": "trading_bot"
        }
        
        auth_url = f"{base_url}?{urlencode(params)}"
        return auth_url
    
    def open_auth_in_browser(self):
        """Open the authorization URL in the default browser."""
        auth_url = self.get_auth_url()
        logger.info(f"🔐 Opening Fyers login in browser...")
        logger.info(f"📎 Auth URL: {auth_url}")
        webbrowser.open(auth_url)
        return auth_url
    
    async def exchange_auth_code(self, auth_code: str) -> Tuple[Optional[str], str]:
        """
        Exchange auth_code for access_token.
        
        Args:
            auth_code: The authorization code from redirect URL
            
        Returns:
            (access_token, error_message)
        """
        try:
            from fyers_apiv3 import fyersModel
            
            session = fyersModel.SessionModel(
                client_id=self.app_id,
                secret_key=self.secret_key,
                redirect_uri=self.redirect_uri,
                response_type="code",
                grant_type="authorization_code"
            )
            
            session.set_token(auth_code)
            response = session.generate_token()
            
            if response.get('s') == 'ok':
                access_token = response['access_token']
                
                # Save token to file
                self._save_token(access_token)
                
                logger.info("✅ Access token generated successfully!")
                return access_token, ""
            else:
                error = response.get('message', 'Unknown error')
                logger.error(f"❌ Token generation failed: {error}")
                return None, error
                
        except Exception as e:
            logger.error(f"❌ Error exchanging auth code: {e}")
            return None, str(e)
    
    def _save_token(self, token: str):
        """Save token to file for persistence."""
        try:
            self.token_file.write_text(token)
            logger.info(f"💾 Token saved to {self.token_file}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save token to file: {e}")

    def load_saved_token(self) -> Optional[str]:
        """Load token from file if exists and valid."""
        try:
            if self.token_file.exists():
                token = self.token_file.read_text().strip()
                is_valid, _ = self.is_token_valid(token)
                if is_valid:
                    return token
        except Exception as e:
            logger.warning(f"⚠️ Could not load saved token: {e}")
        return None

    def get_token_info(self, access_token: Optional[str] = None) -> Dict:
        """Get detailed token information."""
        token = access_token or config.FYERS_ACCESS_TOKEN

        if not token:
            return {
                "has_token": False,
                "is_valid": False,
                "error": "No token configured"
            }

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp')
            exp_datetime = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None

            is_valid, reason = self.is_token_valid(token)

            return {
                "has_token": True,
                "is_valid": is_valid,
                "reason": reason,
                "user_id": decoded.get('fy_id'),
                "expires_at": exp_datetime.isoformat() if exp_datetime else None,
                "time_remaining": str(exp_datetime - datetime.now()) if exp_datetime else None
            }
        except Exception as e:
            return {
                "has_token": True,
                "is_valid": False,
                "error": str(e)
            }

    def _generate_totp(self) -> Optional[str]:
        """
        Generate TOTP code from secret.
        Uses the same algorithm as the working Fyers reference implementation.
        """
        import base64
        import hmac
        import struct
        import time as time_module

        if not self.totp_secret:
            return None
        try:
            key = self.totp_secret.upper()
            # Pad to multiple of 8 for base32 decoding
            key = base64.b32decode(key + "=" * ((8 - len(key)) % 8))
            counter = struct.pack(">Q", int(time_module.time() / 30))
            mac = hmac.new(key, counter, "sha1").digest()
            offset = mac[-1] & 0x0F
            binary = struct.unpack(">L", mac[offset : offset + 4])[0] & 0x7FFFFFFF
            return str(binary)[-6:].zfill(6)
        except Exception as e:
            logger.error(f"❌ TOTP generation failed: {e}")
            return None

    async def auto_login(self) -> Tuple[Optional[str], str]:
        """
        Automatically login using TOTP and get new access token.

        This uses the Fyers API to:
        1. Send OTP request (with base64 encoded fy_id)
        2. Verify with TOTP
        3. Verify PIN (with base64 encoded PIN)
        4. Get auth_code
        5. Exchange for access_token

        Uses sync requests.Session() which maintains cookies between requests.
        This is required for the Fyers API to work correctly.

        Returns:
            (access_token, error_message)
        """
        import base64
        from hashlib import sha256

        if not self.totp_enabled:
            return None, "TOTP auto-login not configured. Set FYERS_TOTP_SECRET and FYERS_PIN in .env"

        if not REQUESTS_AVAILABLE:
            return None, "requests library not available"

        try:
            logger.info("🔐 Starting TOTP auto-login...")

            # Get the Fyers user ID from previous token if available
            fy_id = None
            if config.FYERS_ACCESS_TOKEN:
                try:
                    decoded = jwt.decode(config.FYERS_ACCESS_TOKEN, options={"verify_signature": False})
                    fy_id = decoded.get('fy_id')
                    logger.info(f"📋 Fyers ID from token: {fy_id}")
                except Exception as e:
                    logger.warning(f"Could not decode token: {e}")

            if not fy_id:
                return None, "Could not determine Fyers ID. Please login manually once."

            # Base64 encode the fy_id and PIN as required by Fyers API
            fy_id_encoded = base64.b64encode(fy_id.encode()).decode()
            pin_encoded = base64.b64encode(str(self.pin).encode()).decode()

            logger.info(f"📋 Encoded Fyers ID: {fy_id_encoded}")

            # Use requests.Session() to maintain cookies between requests
            # This is critical - httpx.AsyncClient was failing without session cookies
            session = requests.Session()

            # Step 1: Request OTP using send_login_otp_v2 with BASE64 ENCODED fy_id
            send_otp_url = "https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
            otp_payload = f'{{"fy_id":"{fy_id_encoded}","app_id":"2"}}'

            logger.info(f"📤 Sending OTP request to {send_otp_url}")
            resp = session.post(send_otp_url, data=otp_payload)
            otp_data = resp.json()
            logger.info(f"📥 OTP response: {otp_data.get('s')}")

            if resp.status_code != 200 or otp_data.get('s') == 'error':
                return None, f"OTP request failed (HTTP {resp.status_code}): {otp_data}"

            request_key = otp_data.get('request_key')
            if not request_key:
                return None, f"No request_key in OTP response: {otp_data}"

            logger.info("📲 OTP requested, verifying with TOTP...")

            # Step 2: Verify with TOTP
            totp_code = self._generate_totp()
            if not totp_code:
                return None, "Could not generate TOTP code"
            logger.info(f"🔑 Generated TOTP code: {totp_code}")

            # Use verify_otp endpoint with data= parameter (not content=)
            verify_otp_url = "https://api-t2.fyers.in/vagator/v2/verify_otp"
            verify_payload = f'{{"request_key":"{request_key}","otp":"{totp_code}"}}'

            resp = session.post(verify_otp_url, data=verify_payload)
            verify_data = resp.json()
            logger.info(f"📥 Verify OTP response: {verify_data.get('s')}")

            if resp.status_code != 200 or verify_data.get('s') == 'error':
                return None, f"TOTP verification failed (HTTP {resp.status_code}): {verify_data}"

            request_key = verify_data.get('request_key')
            if not request_key:
                return None, f"No request_key in verify response: {verify_data}"

            logger.info("✅ TOTP verified, verifying PIN...")

            # Step 3: Verify PIN using verify_pin_v2 with BASE64 ENCODED PIN
            verify_pin_url = "https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
            pin_payload = f'{{"request_key":"{request_key}","identity_type":"pin","identifier":"{pin_encoded}"}}'

            resp = session.post(verify_pin_url, data=pin_payload)
            pin_data = resp.json()
            logger.info(f"📥 Verify PIN response: {pin_data.get('s')}")

            if resp.status_code != 200 or pin_data.get('s') == 'error':
                return None, f"PIN verification failed (HTTP {resp.status_code}): {pin_data}"

            access_token_interim = pin_data.get('data', {}).get('access_token')
            if not access_token_interim:
                return None, f"No interim token in PIN response: {pin_data}"

            logger.info("✅ PIN verified, getting auth code...")

            # Step 4: Get auth code using api-t1.fyers.in/api/v3/token
            token_url = "https://api-t1.fyers.in/api/v3/token"
            app_id_only = self.app_id.split('-')[0] if '-' in self.app_id else self.app_id
            token_payload = {
                "fyers_id": fy_id,
                "app_id": app_id_only,
                "redirect_uri": self.redirect_uri,
                "appType": "100",
                "code_challenge": "",
                "state": "trading_bot",
                "scope": "",
                "nonce": "",
                "response_type": "code",
                "create_cookie": True
            }

            resp = session.post(
                token_url,
                json=token_payload,
                headers={"Authorization": f"Bearer {access_token_interim}"}
            )
            token_data = resp.json()
            logger.info(f"📥 Token response: {token_data.get('s')}")

            if token_data.get('s') != 'ok':
                return None, f"Auth code request failed: {token_data}"

            # Extract auth_code from URL
            auth_code_url = token_data.get('Url')
            if not auth_code_url or 'auth_code=' not in auth_code_url:
                return None, f"No auth_code in URL: {auth_code_url}"

            auth_code = auth_code_url.split('auth_code=')[1].split('&')[0]
            logger.info("✅ Got auth code, exchanging for access token...")

            # Step 5: Exchange auth code for final access token
            app_hash = sha256(f"{self.app_id}:{self.secret_key}".encode()).hexdigest()
            validate_url = "https://api-t1.fyers.in/api/v3/validate-authcode"
            validate_payload = {
                "grant_type": "authorization_code",
                "appIdHash": app_hash,
                "code": auth_code
            }

            resp = session.post(validate_url, json=validate_payload)
            final_data = resp.json()
            logger.info(f"📥 Final token response: {final_data.get('s')}")

            if final_data.get('s') != 'ok':
                return None, f"Token exchange failed: {final_data}"

            access_token = final_data.get('access_token')
            if not access_token:
                return None, f"No access_token in response: {final_data}"

            logger.info("🎉 Auto-login successful! Token refreshed.")
            return access_token, ""

        except requests.Timeout:
            return None, "Request timed out - Fyers API may be slow"
        except Exception as e:
            logger.error(f"❌ Auto-login error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None, str(e)

    async def ensure_valid_token(self) -> Tuple[bool, str]:
        """
        Ensure we have a valid token. If expired, try auto-login.

        Returns:
            (success, message)
        """
        is_valid, reason = self.is_token_valid()

        if is_valid:
            return True, reason

        logger.warning(f"⚠️ Token invalid: {reason}")

        # Try to load from file
        saved_token = self.load_saved_token()
        if saved_token:
            logger.info("✅ Loaded valid token from file")
            return True, "Loaded from saved file"

        # Try auto-login if configured
        if self.totp_enabled:
            logger.info("🔄 Attempting TOTP auto-login...")
            access_token, error = await self.auto_login()
            if access_token:
                return True, "Token refreshed via auto-login"
            else:
                return False, f"Auto-login failed: {error}"

        return False, f"Token expired and auto-login not configured. Reason: {reason}"


# Global auth manager instance
fyers_auth = FyersAuthManager()

