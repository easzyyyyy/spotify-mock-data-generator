#!/usr/bin/env python3
"""
Spotify data fetcher module
Provides classes and functions to fetch top tracks and artists from Spotify API
"""

import json
import sys
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class SpotifyTopItems:
    """Client to fetch Spotify top items"""

    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, access_token: str):
        """Initialize the client with access token"""
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_top_items(self, item_type: str, time_range: str = "medium_term",
                      limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Fetch user's top items (tracks or artists)

        Args:
            item_type: "tracks" or "artists"
            time_range: "short_term" (~4 weeks), "medium_term" (~6 months), "long_term" (~1 year)
            limit: Maximum number of items (1-50)
            offset: Starting index

        Returns:
            API response with items
        """
        url = f"{self.BASE_URL}/me/top/{item_type}"
        params = {
            "time_range": time_range,
            "limit": min(limit, 50),
            "offset": offset
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("❌ Error 401: Invalid or expired token")
            elif response.status_code == 403:
                print("❌ Error 403: Access forbidden - Check authorization scopes")
            elif response.status_code == 429:
                print("❌ Error 429: Too many requests - Try again later")
            else:
                print(f"❌ HTTP Error {response.status_code}: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            sys.exit(1)
    def get_all_top_items(self, item_type: str, time_range: str = "medium_term",
                          max_items: int = None, parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all top items with pagination (parallel or sequential)

        Args:
            item_type: "tracks" or "artists"
            time_range: "short_term", "medium_term", "long_term"
            max_items: Maximum number of items to fetch (None = all)
            parallel: Use parallel fetching (default: True)

        Returns:
            List of all items
        """
        print(f"⏳ Fetching top {item_type} ({time_range})...")

        # First request to get total count
        first_data = self.get_top_items(item_type, time_range, limit=50, offset=0)
        all_items = first_data.get("items", [])
        total = first_data.get("total", 0)

        print(f"  ✓ {len(all_items)}/{total} {item_type} fetched...")

        if max_items:
            total = min(total, max_items)

        # Calculate remaining pages to fetch
        remaining = total - len(all_items)
        if remaining <= 0:
            return all_items

        # Generate offsets for remaining pages
        offsets = list(range(50, total, 50))

        if not parallel or len(offsets) == 0:
            # Sequential fetching
            for offset in offsets:
                current_limit = min(50, total - offset)
                data = self.get_top_items(item_type, time_range, current_limit, offset)
                items = data.get("items", [])
                all_items.extend(items)
                print(f"  ✓ {len(all_items)}/{total} {item_type} fetched...")
        else:
            # Parallel fetching (10 requests at a time)
            max_workers = 10

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_offset = {
                    executor.submit(
                        self.get_top_items,
                        item_type,
                        time_range,
                        min(50, total - offset),
                        offset
                    ): offset
                    for offset in offsets
                }

                # Collect results as they complete
                for future in as_completed(future_to_offset):
                    try:
                        data = future.result()
                        items = data.get("items", [])
                        all_items.extend(items)
                        print(f"  ✓ {len(all_items)}/{total} {item_type} fetched...")
                    except Exception as e:
                        offset = future_to_offset[future]
                        print(f"  ⚠️  Failed to fetch at offset {offset}: {e}")

        return all_items[:total]  # Ensure we don't return more than requested
        return all_items


def clean_track_data(tracks: List[Dict[str, Any]], keep_markets: bool = False) -> List[Dict[str, Any]]:
    """
    Clean track data by removing unnecessary fields

    Args:
        tracks: List of track objects
        keep_markets: Whether to keep available_markets field (default: False)

    Returns:
        Cleaned list of tracks
    """
    if keep_markets:
        return tracks

    cleaned_tracks = []
    for track in tracks:
        # Create a copy to avoid modifying original
        cleaned_track = track.copy()

        # Remove available_markets from track
        cleaned_track.pop('available_markets', None)

        # Remove available_markets from album if present
        if 'album' in cleaned_track and isinstance(cleaned_track['album'], dict):
            cleaned_track['album'] = cleaned_track['album'].copy()
            cleaned_track['album'].pop('available_markets', None)

        cleaned_tracks.append(cleaned_track)

    return cleaned_tracks


def save_to_json(data: Dict[str, Any], filename: str):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"📁 File saved: {filename}")
