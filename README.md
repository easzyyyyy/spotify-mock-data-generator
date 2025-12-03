# Spotify Top Tracks & Artists Fetcher

Python script to fetch your top tracks and artists from Spotify API using the `/me/top/{type}` endpoint.

## Features

- ✅ Fetch your top tracks and artists from Spotify
- 🔐 **Automatic OAuth authentication with refresh token**
- ⏱️ Choose time period: last 4 weeks, 6 months, or 1 year
- 🔄 Automatic pagination handling (up to 50 items per request)
- 💾 Export to JSON files
- 🎵 Display your Top 5 tracks and artists

## Prerequisites

- Python 3.7+
- Spotify account
- Spotify Developer App (for automatic authentication)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a Spotify App:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Click "Create app"
   - Add app name and description
   - Set Redirect URI to: `http://127.0.0.1:8888/callback` (use 127.0.0.1, not localhost)
   - Save and copy your **Client ID** and **Client Secret**

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Add your credentials to `.env`:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Usage

**Run the main script:**
```bash
python main.py
```

The script will:
1. Check for existing authentication
2. Ask if you want to refresh or re-authenticate
3. Open browser for login (if needed)
4. Fetch your top tracks and artists
5. Save results to JSON files

**Standalone scripts:**
- `python spotify_auth.py` - Authentication only
- `python spotify_client.py` - Fetch data only (requires token)

## Output Files

The script generates two JSON files:
- `top_tracks_{time_range}.json` - Your top tracks
- `top_artists_{time_range}.json` - Your top artists

Where `{time_range}` is:
- `short_term` - Last ~4 weeks
- `medium_term` - Last ~6 months (default)
- `long_term` - Last ~1 year

## Example Output

```
🎵 Fetch Spotify Top Tracks and Artists
============================================================
🔐 Using automatic authentication...
🔄 Refreshing access token...
✅ Token refreshed successfully!

⚙️  Fetch options:
   1. short_term  - ~last 4 weeks
   2. medium_term - ~last 6 months (default)
   3. long_term   - ~last year

Choose time period (1/2/3) [2]: 2

============================================================
⏳ Fetching top tracks (medium_term)...
  ✓ 50 tracks fetched...
📁 File saved: top_tracks_medium_term.json

============================================================
⏳ Fetching top artists (medium_term)...
  ✓ 50 artists fetched...
📁 File saved: top_artists_medium_term.json

============================================================
✅ Fetch completed successfully!
📊 Statistics:
   • Tracks:  50 fetched → top_tracks_medium_term.json
   • Artists: 50 fetched → top_artists_medium_term.json
   • Period:  medium_term

🎵 Top 5 Tracks:
   1. Song Name - Artist Name
   2. Song Name - Artist Name
   ...

🎤 Top 5 Artists:
   1. Artist Name
   2. Artist Name
   ...
```

## Files

- `main.py` - **Main entry point** (authentication + data fetching)
- `spotify_auth.py` - OAuth authentication manager with refresh token
- `spotify_client.py` - Spotify API client module (SpotifyTopItems class)
- `.env` - Your app credentials (Client ID & Secret)
- `.spotify_tokens.json` - Access & refresh tokens (auto-generated, auto-refreshed)

## API Reference

This script uses the Spotify Web API endpoint:
- `GET /me/top/{type}` - Get user's top artists or tracks

Documentation: [Spotify API - Get User's Top Items](https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks)

## Troubleshooting

### Error 401: Invalid or expired token
Run `python spotify_auth.py` to refresh your authentication.

### Error 403: Access forbidden
Make sure your Spotify app has the correct redirect URI: `http://127.0.0.1:8888/callback`

### Error 429: Too many requests
You've hit the rate limit. Wait a few moments and try again.

### "Redirect URI mismatch" or "INVALID_CLIENT"
Check that `http://127.0.0.1:8888/callback` is added to your app settings in the Spotify Dashboard. Note: Use `127.0.0.1` instead of `localhost` (Spotify requirement since April 2025). app settings in the Spotify Dashboard. Note: Use `127.0.0.1` instead of `localhost` (Spotify requirement since April 2025).
You've hit the rate limit. Wait a few moments and try again.

## License

MIT
