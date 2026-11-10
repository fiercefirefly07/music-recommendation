"""Spotify's native browser player, shown directly on each song card.

The native Embed Play control receives the click itself. A Streamlit button
would first cause a server rerun, which cannot carry that browser click through
to Spotify's player and therefore requires an extra click.
"""

from __future__ import annotations

import re

import streamlit.components.v1 as components


TRACK_URI = re.compile(r"spotify:track:([A-Za-z0-9]{22})\Z")


def browser_player_url(track_uri: str) -> str:
    match = TRACK_URI.fullmatch(track_uri)
    if not match:
        raise ValueError("A Spotify track URI is required for browser playback")
    return f"https://open.spotify.com/embed/track/{match.group(1)}"


def render_browser_play_button(track: dict) -> None:
    """Let Spotify's own visible Play control start this song in one click."""
    components.iframe(
        browser_player_url(track.get("uri", "")),
        height=152,
        scrolling=False,
    )
