#!/usr/bin/env python3
"""
Main entry point for Spotify Top Tracks & Artists Fetcher
Handles authentication, token management, and data fetching
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from spotify_auth import SpotifyAuth, get_valid_token
from spotify_client import SpotifyTopItems, save_to_json, clean_track_data


def setup_authentication():
    """Setup Spotify authentication"""
    print("🔐 Spotify Authentication Setup")
    print("=" * 60)

    # Load environment
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("\n❌ Missing Spotify credentials!")
        print("\nPlease add to your .env file:")
        print("SPOTIFY_CLIENT_ID=your_client_id")
        print("SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("\nGet them from: https://developer.spotify.com/dashboard")
        print("Set Redirect URI to: http://127.0.0.1:8888/callback")
        return None

    print(f"✓ Client ID found: {client_id[:20]}...")

    # Check for existing tokens
    auth = SpotifyAuth(client_id, client_secret)
    tokens = auth.load_tokens()

    if tokens and 'refresh_token' in tokens:
        print("✓ Existing tokens found")
        print("\n🔄 Options:")
        print("1. Use existing token (refresh if needed)")
        print("2. Re-authenticate (new login)")
        choice = input("\nChoice (1/2) [1]: ").strip() or "1"

        if choice == "1":
            try:
                print("\n🔄 Refreshing access token...")
                token = get_valid_token()
                if token:
                    print("✅ Token refreshed successfully!")
                    return token
            except Exception as e:
                print(f"⚠️  Could not refresh token: {e}")
                print("Starting new authentication flow...\n")

    # Start new authentication
    print("\n🌐 Starting authentication flow...")
    auth.start_auth_flow()

    # Load newly saved tokens
    tokens = auth.load_tokens()
    return tokens.get('access_token')


def fetch_data(access_token: str):
    """Fetch top tracks and artists"""
    print("\n" + "=" * 60)
    print("🎵 Fetch Spotify Top Tracks and Artists")
    print("=" * 60)

    # Initialize client
    client = SpotifyTopItems(access_token)

    # Ask for time range
    print("\n⚙️  Fetch options:")
    print("   1. short_term  - ~last 4 weeks")
    print("   2. medium_term - ~last 6 months (default)")
    print("   3. long_term   - ~last year")

    time_range_choice = input("\nChoose time period (1/2/3) [2]: ").strip() or "2"
    time_ranges = {"1": "short_term", "2": "medium_term", "3": "long_term"}
    time_range = time_ranges.get(time_range_choice, "medium_term")

    # Ask about available_markets
    print("\n💾 Data optimization:")
    print("   Keep 'available_markets' field? (increases file size significantly)")
    keep_markets = input("   (y/N) [N]: ").strip().lower() in ['y', 'yes']

    # Fetch tracks
    print("\n" + "=" * 60)
    tracks = client.get_all_top_items("tracks", time_range)

    # Clean track data if needed
    if not keep_markets:
        print("🧹 Removing 'available_markets' fields to reduce file size...")
        tracks = clean_track_data(tracks, keep_markets=False)

    tracks_data = {"items": tracks}

    tracks_filename = f"top_tracks_{time_range}.json"
    save_to_json(tracks_data, tracks_filename)

    # Fetch artists
    print("\n" + "=" * 60)
    artists = client.get_all_top_items("artists", time_range)
    artists_data = {"items": artists}

    artists_filename = f"top_artists_{time_range}.json"
    save_to_json(artists_data, artists_filename)

    # Summary
    print("\n" + "=" * 60)
    print("✅ Fetch completed successfully!")
    print(f"📊 Statistics:")
    print(f"   • Tracks:  {len(tracks)} fetched → {tracks_filename}")
    print(f"   • Artists: {len(artists)} fetched → {artists_filename}")
    print(f"   • Period:  {time_range}")

    # Top 5 tracks
    if tracks:
        print(f"\n🎵 Top 5 Tracks:")
        for i, track in enumerate(tracks[:5], 1):
            artist_names = ", ".join([a["name"] for a in track["artists"]])
            print(f"   {i}. {track['name']} - {artist_names}")

    # Top 5 artists
    if artists:
        print(f"\n🎤 Top 5 Artists:")
        for i, artist in enumerate(artists[:5], 1):
            print(f"   {i}. {artist['name']}")


def main():
    """Main function"""
    print("\n" + "🎵" * 30)
    print("   Spotify Top Tracks & Artists Fetcher")
    print("🎵" * 30 + "\n")

    try:
        # Setup authentication and get token
        access_token = setup_authentication()

        if not access_token:
            print("\n❌ Authentication failed!")
            sys.exit(1)

        # Fetch data
        fetch_data(access_token)

        print("\n" + "=" * 60)
        print("✨ All done! Thank you for using Spotify Fetcher ✨")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
