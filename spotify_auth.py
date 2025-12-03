#!/usr/bin/env python3
"""
Spotify Authentication with OAuth 2.0 and Refresh Token
Provides a simple interface to authenticate and get access tokens
"""

import os
import json
import base64
import webbrowser
from pathlib import Path
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv, set_key


class SpotifyAuth:
    """Handle Spotify OAuth 2.0 authentication with refresh token"""

    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    REDIRECT_URI = "http://127.0.0.1:8888/callback"
    SCOPE = "user-top-read user-read-private user-read-email"

    def __init__(self, client_id: str, client_secret: str):
        """Initialize with Spotify app credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.token_file = Path(__file__).parent / '.spotify_tokens.json'
        self.env_file = Path(__file__).parent / '.env'

    def get_auth_url(self) -> str:
        """Generate authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.REDIRECT_URI,
            'scope': self.SCOPE,
            'show_dialog': 'true'
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def get_tokens_from_code(self, code: str) -> dict:
        """Exchange authorization code for access and refresh tokens"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.REDIRECT_URI
        }

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Get new access token using refresh token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    def save_tokens(self, tokens: dict):
        """Save tokens to JSON file only"""
        # Save to JSON file with timestamp
        tokens['expires_at'] = tokens.get('expires_in', 3600)  # Default 1 hour
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=4)

        print(f"✅ Tokens saved to {self.token_file}")

    def load_tokens(self) -> dict:
        """Load tokens from file"""
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                return json.load(f)
        return {}

    def start_auth_flow(self):
        """Start the OAuth flow with local server"""
        auth_url = self.get_auth_url()

        print("\n🔐 Spotify Authentication")
        print("=" * 60)
        print("\n1. Opening browser for authentication...")
        print("2. After authorizing, you'll be redirected to 127.0.0.1:8888")
        print("3. The token will be saved automatically\n")

        # Start local server to receive callback
        server = AuthCallbackServer(self)

        # Open browser
        webbrowser.open(auth_url)

        print("⏳ Waiting for authentication...\n")
        server.serve_forever()


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""

    def do_GET(self):
        """Handle GET request from OAuth callback"""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            code = params['code'][0]

            # Get tokens
            try:
                tokens = self.server.auth.get_tokens_from_code(code)
                self.server.auth.save_tokens(tokens)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                html = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #1DB954;">✅ Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

                print("✅ Authentication successful!")
                print(f"📁 Access token: {tokens['access_token'][:20]}...")
                if 'refresh_token' in tokens:
                    print(f"🔄 Refresh token: {tokens['refresh_token'][:20]}...")

                # Stop server
                self.server.should_stop = True

            except Exception as e:
                print(f"❌ Error getting tokens: {e}")
                self.send_error(500, f"Error: {e}")

        elif 'error' in params:
            error = params['error'][0]
            self.send_error(400, f"Authentication error: {error}")
            print(f"❌ Authentication error: {error}")
            self.server.should_stop = True

        else:
            self.send_error(400, "Invalid callback")

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class AuthCallbackServer(HTTPServer):
    """HTTP server for OAuth callback"""

    def __init__(self, auth):
        self.auth = auth
        self.should_stop = False
        super().__init__(('127.0.0.1', 8888), AuthCallbackHandler)

    def serve_forever(self):
        """Serve until authentication complete"""
        while not self.should_stop:
            self.handle_request()


def get_valid_token() -> str:
    """Get a valid access token (refresh if needed)"""
    load_dotenv()

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')

    if not client_id or not client_secret:
        print("❌ SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET required in .env")
        return None

    auth = SpotifyAuth(client_id, client_secret)

    # Try to load existing tokens
    tokens = auth.load_tokens()

    if refresh_token or tokens.get('refresh_token'):
        # Try to refresh token
        try:
            print("🔄 Refreshing access token...")
            refresh_tok = refresh_token or tokens['refresh_token']
            new_tokens = auth.refresh_access_token(refresh_tok)

            # Keep the old refresh token if new one not provided
            if 'refresh_token' not in new_tokens:
                new_tokens['refresh_token'] = refresh_tok

            auth.save_tokens(new_tokens)
            print("✅ Token refreshed successfully!")
            return new_tokens['access_token']
        except Exception as e:
            print(f"⚠️  Could not refresh token: {e}")
            print("Starting new authentication flow...\n")

    # Start new auth flow
    auth.start_auth_flow()

    # Load newly saved tokens
    tokens = auth.load_tokens()
    return tokens.get('access_token')


def main():
    """Main function for standalone use"""
    print("🎵 Spotify Authentication Manager")
    print("=" * 60)

    # Load environment
    load_dotenv()

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("\n❌ Missing Spotify credentials!")
        print("\nPlease add to your .env file:")
        print("SPOTIFY_CLIENT_ID=your_client_id")
        print("SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("\nGet them from: https://developer.spotify.com/dashboard")
        return

    print(f"\n✓ Client ID found: {client_id[:20]}...")

    # Check for existing tokens
    auth = SpotifyAuth(client_id, client_secret)
    tokens = auth.load_tokens()

    if tokens and 'refresh_token' in tokens:
        print("\n🔄 Existing tokens found. Options:")
        print("1. Refresh existing token")
        print("2. Start new authentication")
        choice = input("\nChoice (1/2) [1]: ").strip() or "1"

        if choice == "1":
            token = get_valid_token()
            if token:
                print(f"\n✅ Access token ready: {token[:30]}...")
            return

    # Start new authentication
    auth.start_auth_flow()


if __name__ == "__main__":
    main()
