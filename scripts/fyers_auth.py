#!/usr/bin/env python3
"""
Fyers API Authentication Helper
Generates access token for Fyers API authentication.
"""

import sys
import os
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from config import get_config

def generate_fyers_access_token():
    """Generate Fyers access token using OAuth2 flow."""
    try:
        from fyers_apiv3 import fyersModel
        
        config = get_config()
        
        if not config.FYERS_APP_ID or not config.FYERS_SECRET_KEY:
            print("❌ Error: FYERS_APP_ID and FYERS_SECRET_KEY must be set in .env file")
            return None
        
        # Create session for authentication
        session = fyersModel.SessionModel(
            client_id=config.FYERS_APP_ID,
            secret_key=config.FYERS_SECRET_KEY,
            redirect_uri=config.FYERS_REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )
        
        # Generate authorization URL
        auth_url = session.generate_authcode()
        print(f"🔗 Please visit this URL to authorize the application:")
        print(f"{auth_url}")
        print()
        print("📝 After authorization, you will be redirected to a URL.")
        print("📝 Copy the authorization code from the URL and paste it below.")
        print()
        
        # Get authorization code from user
        auth_code = input("🔑 Enter the authorization code: ").strip()
        
        if not auth_code:
            print("❌ Error: Authorization code is required")
            return None
        
        # Debug info
        print()
        print("🔧 Debug Info:")
        print(f"   App ID: {config.FYERS_APP_ID}")
        print(f"   Secret Key: {config.FYERS_SECRET_KEY[:4]}...{config.FYERS_SECRET_KEY[-2:]}")
        print(f"   Redirect URI: {config.FYERS_REDIRECT_URI}")
        print(f"   Auth Code (first 50 chars): {auth_code[:50]}...")
        print()

        # Set authorization code
        session.set_token(auth_code)

        # Generate access token
        print("🔄 Generating access token...")
        response = session.generate_token()

        print(f"📥 Full Response: {response}")
        print()

        if response.get('s') == 'ok':
            access_token = response['access_token']
            print(f"✅ Access token generated successfully!")
            print(f"🔑 Access Token: {access_token}")
            print()
            print("📝 Add this to your .env file:")
            print(f"FYERS_ACCESS_TOKEN={access_token}")
            print()
            print("⚠️  Note: This token is valid for the trading day. You may need to regenerate it daily.")

            # Optionally update .env file
            update_env = input("🔄 Do you want to automatically update the .env file? (y/n): ").strip().lower()
            if update_env == 'y':
                update_env_file(access_token)

            return access_token
        else:
            print(f"❌ Error generating access token: {response}")
            print()

            # Provide helpful error messages
            error_code = response.get('code')
            if error_code == -5:
                print("⚠️  Error -5: 'invalid app id hash'")
                print()
                print("💡 This usually means:")
                print("   1. App ID and Secret Key don't match")
                print("   2. Secret Key might be incorrect")
                print("   3. Authorization code might have expired (valid for ~5 minutes)")
                print()
                print("🔍 Please verify in Fyers Dashboard:")
                print("   1. Go to: https://myapi.fyers.in/dashboard")
                print("   2. Check your App ID matches: 1SD1DZHQVT-100")
                print("   3. Regenerate Secret Key if needed")
                print("   4. Try the authentication flow again with a fresh auth code")

            return None
            
    except ImportError:
        print("❌ Error: fyers-apiv3 package not found. Install it using:")
        print("pip install fyers-apiv3")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def update_env_file(access_token):
    """Update .env file with the new access token."""
    try:
        env_path = Path(__file__).parent.parent / ".env"
        
        if env_path.exists():
            # Read existing content
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Update or add access token
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith('FYERS_ACCESS_TOKEN='):
                    lines[i] = f'FYERS_ACCESS_TOKEN={access_token}'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'FYERS_ACCESS_TOKEN={access_token}')
            
            # Write updated content
            with open(env_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Updated .env file with new access token")
        else:
            print(f"❌ .env file not found at {env_path}")
            
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")

def test_fyers_connection():
    """Test Fyers API connection with current credentials."""
    try:
        from fyers_apiv3 import fyersModel
        
        config = get_config()
        
        if not config.FYERS_ACCESS_TOKEN:
            print("❌ Error: FYERS_ACCESS_TOKEN not set. Run authentication first.")
            return False
        
        # Initialize Fyers API
        fyers = fyersModel.FyersModel(
            client_id=config.FYERS_APP_ID,
            is_async=False,
            token=config.FYERS_ACCESS_TOKEN,
            log_path=""
        )
        
        # Test connection
        print("🔌 Testing Fyers API connection...")
        profile = fyers.get_profile()
        
        if profile['s'] == 'ok':
            print("✅ Fyers API connection successful!")
            print(f"📊 Account: {profile['data']['name']}")
            print(f"🆔 Client ID: {profile['data']['fyersId']}")
            return True
        else:
            print(f"❌ Fyers API connection failed: {profile}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Fyers API Authentication Helper")
    print("=" * 40)
    
    import argparse
    parser = argparse.ArgumentParser(description="Fyers API Authentication Helper")
    parser.add_argument("--auth", action="store_true", help="Generate new access token")
    parser.add_argument("--test", action="store_true", help="Test current connection")
    
    args = parser.parse_args()
    
    if args.auth:
        generate_fyers_access_token()
    elif args.test:
        test_fyers_connection()
    else:
        print("📝 Usage:")
        print("  python fyers_auth.py --auth   # Generate new access token")
        print("  python fyers_auth.py --test   # Test current connection")
