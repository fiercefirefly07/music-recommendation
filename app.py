
import time
import re
import os
from html import escape
from pathlib import Path

import av
import cv2
import spotipy
import streamlit as st
from dotenv import load_dotenv

from spotipy.oauth2 import SpotifyOAuth
from streamlit_webrtc import (
    WebRtcMode,
    VideoProcessorBase,
    webrtc_streamer,
)

from emotion_tracker import EmotionTracker
from browser_player import TRACK_URI, render_browser_play_button
from music import LANGUAGES, Seed, _resolve, matches_genre, recommend as curated_recommend
from recommendation_engine import (
    MOOD_QUERIES,
    get_insights,
    get_queries,
    load_preferences,
    rank_tracks,
    record_play,
    save_preferences,
    toggle_dislike,
    toggle_favorite,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Emotion Music 3.0",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)
cache_setting = os.getenv("SPOTIPY_CACHE_PATH", ".spotify_cache")
CACHE_FILE = Path(cache_setting)
if not CACHE_FILE.is_absolute():
    CACHE_FILE = BASE_DIR / CACHE_FILE

RTC_CONFIGURATION = {
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
}

MOOD_EMOJIS = {
    "happy": "😄",
    "sad": "😢",
    "neutral": "😌",
    "angry": "😠",
    "fear": "😨",
    "surprise": "😲",
    "disgust": "😖",
}

GENRES = [
    "Any",
    "Pop",
    "Rock",
    "Hip-Hop",
    "Dance",
    "Electronic",
    "Indie",
    "Acoustic",
    "Ambient",
    "Instrumental",
    "Classical",
]

PAGES = [
    "Discover",
    "Mood Studio",
    "Favorites",
    "Listening Insights",
]


# ==================================================
# UI THEME
# ==================================================

st.markdown(
    "<style>" + (BASE_DIR / "assets" / "theme.css").read_text(encoding="utf-8") + "</style>",
    unsafe_allow_html=True,
)

# ==================================================
# SESSION STATE
# ==================================================

if "preferences" not in st.session_state:
    st.session_state.preferences = load_preferences()

DEFAULTS = {
    "mood": "happy",
    "auto_mood": True,
    "spotify_token": None,
    "playback_message": None,
    "playback_error": None,
    "browser_track": None,
    "browser_playback": False,
    "selected_device_id": None,
    "spotify_cache_scope": "",
    "navigation": "Discover",
    "detected_mood": None,
    "detected_confidence": 0.0,
}

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


# ==================================================
# EMOTION VIDEO PROCESSOR
# ==================================================

class EmotionVideoProcessor(VideoProcessorBase):

    def __init__(self):
        self.tracker = EmotionTracker()

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        self.tracker.submit(image)
        snapshot = self.tracker.snapshot()
        if snapshot.box:
            x, y, w, h = snapshot.box
            color = (238, 116, 175) if snapshot.face_visible else (155, 120, 150)
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        label = (
            f"{snapshot.emotion.upper()} {snapshot.confidence:.0f}%"
            if snapshot.emotion else "LOOKING FOR FACE"
        )

        cv2.rectangle(
            image,
            (8, 8),
            (min(460, image.shape[1] - 1), 62),
            (30, 15, 50),
            -1,
        )

        cv2.putText(
            image,
            label[:35],
            (20, 43),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (220, 150, 255),
            2,
        )

        return av.VideoFrame.from_ndarray(
            image,
            format="bgr24",
        )

    def get_status(self):
        snapshot = self.tracker.snapshot()
        status = (
            "Tracking face" if snapshot.face_visible else
            "Holding last reading" if snapshot.face_recent else
            "Looking for a face"
        )
        return {"status": status, "error": snapshot.error}

    def on_ended(self):
        self.tracker.close()


# ==================================================
# SPOTIFY AUTHENTICATION
# ==================================================

def spotify_setting(name: str) -> str:
    try:
        value = st.secrets.get(name)
    except FileNotFoundError:
        value = None
    return str(value).strip() if value else os.getenv(name, "").strip()


def auth_manager():
    settings = {
        name: spotify_setting(name)
        for name in (
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "SPOTIFY_REDIRECT_URI",
        )
    }
    missing = [name for name, value in settings.items() if not value]
    if missing:
        raise RuntimeError(
            "Spotify settings are missing: " + ", ".join(missing) + ". "
            "Set them in .streamlit/secrets.toml or .env."
        )
    return SpotifyOAuth(
        client_id=settings["SPOTIFY_CLIENT_ID"],
        client_secret=settings["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=settings["SPOTIFY_REDIRECT_URI"],
        scope=(
            "user-read-private "
            "user-read-email "
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-read-currently-playing"
        ),
        cache_path=str(CACHE_FILE),
        open_browser=False,
    )


def connect_spotify():
    auth = auth_manager()

    oauth_error = st.query_params.get("error")

    if oauth_error:
        st.error(
            f"Spotify login failed: {oauth_error}"
        )
        st.stop()

    code = st.query_params.get("code")

    if code:
        token = auth.get_access_token(
            code,
            check_cache=False,
        )

        st.session_state.spotify_token = token
        st.query_params.clear()
        st.rerun()

    token = st.session_state.spotify_token

    if not token:
        token = auth.get_cached_token()

    if token and auth.is_token_expired(token):
        token = auth.refresh_access_token(
            token["refresh_token"]
        )

    if not token:
        st.markdown(
            """
            <div class="hero">
                <div class="hero-label">
                    WELCOME TO THE FUTURE
                </div>
                <div class="hero-title">
                    Emotion Music 3.0 💜
                </div>
                <div class="hero-subtitle">
                    Connect Spotify to discover
                    your personal soundtrack.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.link_button(
            "Connect Spotify",
            auth.get_authorize_url(),
            type="primary",
        )

        st.stop()

    st.session_state.spotify_token = token

    return spotipy.Spotify(
        auth_manager=auth,
        requests_timeout=10,
        retries=1,
    )


# ==================================================
# SPOTIFY TRACK NORMALIZATION
# ==================================================

def normalize_track(item):
    if not item or not item.get("uri"):
        return None

    album = item.get("album") or {}
    images = album.get("images") or []

    artists = [
        artist.get("name", "")
        for artist in item.get("artists", [])
    ]

    return {
        "id": item["uri"],
        "uri": item["uri"],
        "album_uri": album.get("uri"),
        "title": item.get("name", "Unknown"),
        "artist": ", ".join(artists),
        "artists": artists,
        "album": album.get("name", ""),
        "image": (
            images[0]["url"]
            if images
            else None
        ),
        "url": (
            item.get("external_urls") or {}
        ).get("spotify", ""),
    }


# ==================================================
# SPOTIFY SEARCH
# ==================================================

@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def search_spotify(query, account_scope, _access_token):
    client = spotipy.Spotify(
        auth=_access_token,
        requests_timeout=10,
        retries=1,
    )

    return client.search(
        q=query,
        type="track",
        limit=10,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def resolve_seed_cached(seed_title: str, seed_artist: str,
                        account_scope: str, _access_token: str):
    client = spotipy.Spotify(auth=_access_token, requests_timeout=10, retries=1)
    return _resolve(client, Seed(seed_title, seed_artist, ""))


def resolve_seed_for_recommendation(seed: Seed, account_scope: str,
                                    access_token: str):
    resolved = resolve_seed_cached(
        seed.title, seed.artist, account_scope, access_token,
    )
    if resolved is None:
        return None
    return {
        **resolved,
        "reason": seed.why,
        "language": seed.language,
        "seed_genres": seed.genres,
    }


def curated_tracks(access_token, account_scope, mood, mode, language, count):
    direction = "Improve" if mode == "Improve My Mood" else "Match"
    return curated_recommend(
        None, mood, direction, count=count, language=language,
        resolver=lambda seed: resolve_seed_for_recommendation(
            seed, account_scope, access_token,
        ),
    )


def discover_tracks(
    mood,
    mode,
    genre,
    language,
    search,
    limit,
):
    access_token = (
        st.session_state.spotify_token[
            "access_token"
        ]
    )

    preferences = st.session_state.preferences
    account_scope = st.session_state.spotify_cache_scope
    curated = []
    if not search.strip() or language != "Any":
        curated = [
            track for track in curated_tracks(
                access_token, account_scope, mood, mode, language,
                count=limit if genre == "Any" else 30,
            )
            if matches_genre(track, genre)
        ]
        if search.strip():
            term = search.casefold().strip()
            curated = [track for track in curated if term in
                       f"{track['title']} {track['artist']}".casefold()]
        curated = rank_tracks(curated, preferences, mood, mode)
        for track in curated:
            track["reasons"] = [track.get("reason", "Editorial mood pick"), *track["reasons"]]

    if language != "Any" or len(curated) >= limit:
        return curated[:limit]

    queries = get_queries(mood, mode, genre, search)
    found = {}

    for query in queries:
        response = search_spotify(
            query,
            account_scope,
            access_token,
        )

        items = (
            response.get("tracks") or {}
        ).get("items", [])

        for item in items:
            track = normalize_track(item)

            if track and track["id"] not in {item["id"] for item in curated}:
                found[track["id"]] = track

    ranked = rank_tracks(
        list(found.values()),
        preferences,
        mood,
        mode,
    )
    for track in ranked:
        track["reasons"] = [
            "Broader Spotify discovery; expression fit may vary",
            *track["reasons"],
        ]
    return (curated + ranked)[:limit]


# ==================================================
# VERIFIED SPOTIFY PLAYBACK
# ==================================================

def verify_playback(
    spotify,
    track_uri,
    device_id,
):
    last_state = None

    for _ in range(2):
        time.sleep(0.3)

        last_state = spotify.current_playback()

        if not last_state:
            continue

        item = last_state.get("item") or {}
        device = last_state.get("device") or {}

        if (
            last_state.get("is_playing")
            and item.get("uri") == track_uri
            and (
                device_id is None
                or device.get("id") == device_id
            )
        ):
            return True, last_state

    return False, last_state


def play_track(spotify, track):
    st.session_state.playback_message = None
    st.session_state.playback_error = None
    st.session_state.browser_track = None

    track_uri = track.get("uri")
    album_uri = track.get("album_uri")

    if not track_uri or not album_uri:
        st.session_state.playback_error = (
            "Album-context playback is unavailable "
            "for this track. Open it in Spotify."
        )
        return

    try:
        devices = spotify.devices().get("devices", [])
        available = [
            device for device in devices
            if device.get("id") and not device.get("is_restricted")
        ]
        if not available:
            st.session_state.browser_track = track
            st.session_state.playback_message = (
                "No Spotify Connect device is available. Use the player below "
                "to listen in this browser."
            )
            return

        preferred_id = st.session_state.selected_device_id
        target = next(
            (device for device in available if device["id"] == preferred_id),
            None,
        ) or next(
            (device for device in available if device.get("is_active")),
            available[0],
        )
        device_id = target["id"]
        if not target.get("is_active"):
            spotify.transfer_playback(device_id, force_play=False)
            # Spotify can take a moment to make a transferred device active.
            for _ in range(2):
                time.sleep(0.3)
                updated = spotify.devices().get("devices", [])
                if any(
                    device.get("id") == device_id and device.get("is_active")
                    for device in updated
                ):
                    break

        # IMPORTANT:
        # This is the method that worked
        # on your laptop.
        #
        # Do not use uris=[track_uri].
        # Do not pass device_id here.

        spotify.start_playback(
            context_uri=album_uri,
            offset={"uri": track_uri},
        )

        record_play(
            st.session_state.preferences,
            track,
            st.session_state.mood,
        )

        verified, state = verify_playback(
            spotify,
            track_uri,
            device_id,
        )

        if verified:
            st.session_state.playback_message = (
                f"🎵 Now playing: {track['title']}"
            )

        else:
            st.session_state.playback_message = (
                f"Playback sent to {target.get('name', 'Spotify')}. "
                "The live player may take a moment to update."
            )

    except spotipy.SpotifyException as error:
        if error.http_status == 404:
            st.session_state.playback_error = (
                "Spotify could not activate that device. Refresh the device list "
                "and try again, or use the browser player if none appears."
            )
        else:
            st.session_state.playback_error = str(error)
    except Exception as error:
        st.session_state.playback_error = str(error)


def playback_command(action):
    try:
        action()

        st.session_state.playback_error = None

    except Exception as error:
        st.session_state.playback_error = str(error)


# ==================================================
# SONG CARDS
# ==================================================

def show_tracks(tracks, section, spotify):
    if not tracks:
        detail = (
            "Try another mood, genre, or language."
            if section == "discovery"
            else "Songs you save and select will appear here."
        )
        st.markdown(
            '<div class="empty-state"><strong>Nothing in this mix yet</strong>'
            + detail + '</div>',
            unsafe_allow_html=True,
        )
        return

    for start in range(0, len(tracks), 3):
        columns = st.columns(
            3,
            gap="medium",
        )

        for index, track in enumerate(
            tracks[start:start + 3]
        ):
            with columns[index]:
                with st.container(border=True):
                    st.markdown(
                        f'<div class="eyebrow">'
                        f'{start + index + 1:02d} / {escape(section.upper())}'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    if track.get("image"):
                        st.image(
                            track["image"],
                            width="stretch",
                        )
                    else:
                        st.markdown("### 🎵")

                    st.markdown(
                        f"**{track['title']}**"
                    )

                    st.caption(
                        track.get("artist", "")
                    )

                    st.caption(
                        track.get("album", "")
                    )

                    if "score" in track:
                        st.markdown(
                            f'<div class="score">'
                            f'✦ RANKING SCORE '
                            f'{track["score"]:.0f}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    browser_player = st.session_state.browser_playback and TRACK_URI.fullmatch(
                        track.get("uri") or ""
                    )
                    if browser_player:
                        render_browser_play_button(track)
                        fav_col, dislike_col = st.columns(2)
                    else:
                        play_col, fav_col, dislike_col = st.columns([2, 1, 1])
                        with play_col:
                            if st.button(
                                "▶ Play",
                                key=(
                                    f"{section}_play_"
                                    f"{track['id']}"
                                ),
                                use_container_width=True,
                                type="primary",
                            ):
                                play_track(
                                    spotify,
                                    track,
                                )
                                st.rerun()

                    with fav_col:
                        liked = (
                            track["id"]
                            in st.session_state.preferences[
                                "favorites"
                            ]
                        )

                        if st.button(
                            "💜" if liked else "🤍",
                            key=(
                                f"{section}_fav_"
                                f"{track['id']}"
                            ),
                        ):
                            toggle_favorite(
                                st.session_state.preferences,
                                track,
                            )
                            st.rerun()

                    with dislike_col:
                        disliked = (
                            track["id"]
                            in st.session_state.preferences[
                                "dislikes"
                            ]
                        )

                        if st.button(
                            "👎" if disliked else "➖",
                            key=(
                                f"{section}_dis_"
                                f"{track['id']}"
                            ),
                        ):
                            toggle_dislike(
                                st.session_state.preferences,
                                track,
                            )
                            st.rerun()

                    if track.get("reasons"):
                        with st.expander(
                            "✦ Why this song?"
                        ):
                            for reason in track["reasons"]:
                                st.write("•", reason)

                    if track.get("url"):
                        st.link_button(
                            "Open in Spotify ↗",
                            track["url"],
                            use_container_width=True,
                        )


# ==================================================
# LIVE SPOTIFY PLAYER
# ==================================================

@st.fragment(run_every="3s")
def live_player(spotify):
    try:
        playback = spotify.current_playback()

    except Exception as error:
        st.warning(str(error))
        return

    if not playback or not playback.get("item"):
        st.markdown(
            '<div class="empty-state"><strong>Waiting for a Spotify Connect session</strong>'
            'Songs played in the in-page browser player stay on their song card. '
            'This live panel appears when you use an active Spotify device.</div>',
            unsafe_allow_html=True,
        )
        return

    item = playback["item"]
    album = item.get("album") or {}
    images = album.get("images") or []

    with st.container(border=True):
        artwork, details = st.columns([1, 4])

        with artwork:
            if images:
                st.image(
                    images[0]["url"],
                    width="stretch",
                )

        with details:
            st.markdown(
                '<div class="eyebrow">'
                'NOW PLAYING'
                '</div>',
                unsafe_allow_html=True,
            )

            st.subheader(
                item.get("name", "Unknown")
            )

            artists = ", ".join(
                artist.get("name", "")
                for artist in item.get("artists", [])
            )

            st.caption(artists)

            progress = (
                playback.get("progress_ms") or 0
            )

            duration = (
                item.get("duration_ms") or 0
            )

            if duration > 0:
                st.progress(
                    min(
                        1.0,
                        max(0.0, progress / duration),
                    )
                )

                st.caption(
                    f"{progress // 60000}:"
                    f"{(progress // 1000) % 60:02d}"
                    " / "
                    f"{duration // 60000}:"
                    f"{(duration // 1000) % 60:02d}"
                )

        device = playback.get("device") or {}

        st.caption(
            f"🔊 {device.get('name', 'Unknown')}"
        )

        previous, toggle, next_button = (
            st.columns(3)
        )

        with previous:
            if st.button(
                "⏮ Previous",
                key="player_previous",
                use_container_width=True,
            ):
                playback_command(
                    spotify.previous_track
                )
                st.rerun(scope="fragment")

        with toggle:
            if playback.get("is_playing"):
                if st.button(
                    "⏸ Pause",
                    key="player_pause",
                    type="primary",
                    use_container_width=True,
                ):
                    playback_command(
                        spotify.pause_playback
                    )
                    st.rerun(scope="fragment")

            else:
                if st.button(
                    "▶ Resume",
                    key="player_resume",
                    type="primary",
                    use_container_width=True,
                ):
                    playback_command(
                        spotify.start_playback
                    )
                    st.rerun(scope="fragment")

        with next_button:
            if st.button(
                "⏭ Next",
                key="player_next",
                use_container_width=True,
            ):
                playback_command(
                    spotify.next_track
                )
                st.rerun(scope="fragment")


# ==================================================
# CONNECT SPOTIFY
# ==================================================

try:
    spotify = connect_spotify()
    profile = spotify.current_user()
    st.session_state.spotify_cache_scope = (
        f"{profile.get('id', '')}:{profile.get('country', '')}"
    )

except Exception as error:
    st.error(
        f"Spotify connection failed: {error}"
    )
    st.stop()


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-icon">EM</div>'
        '<div><div class="sidebar-brand-name">EMOTION MUSIC</div>'
        '<div class="sidebar-brand-sub">YOUR SOUNDTRACK · 3.0</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        '<div class="connection-pill">Spotify connected · '
        + escape(profile.get("display_name") or "Your account")
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-eyebrow">Navigate</div>', unsafe_allow_html=True)
    navigation = st.radio(
        "Explore",
        PAGES,
        key="navigation",
    )

    st.divider()

    st.markdown('<div class="sidebar-eyebrow">Emotion control</div>', unsafe_allow_html=True)

    st.toggle(
        "Automatic detection",
        key="auto_mood",
    )

    if not st.session_state.auto_mood:
        st.selectbox(
            "Your mood",
            list(MOOD_QUERIES),
            format_func=lambda mood: (
                f"{MOOD_EMOJIS[mood]} "
                f"{mood.title()}"
            ),
            key="mood",
        )

    saved_mode = (
        st.session_state.preferences["mode"]
    )

    mode = st.radio(
        "Recommendation mode",
        [
            "Match My Mood",
            "Improve My Mood",
        ],
        index=(
            1
            if saved_mode == "Improve My Mood"
            else 0
        ),
    )

    st.markdown('<div class="sidebar-eyebrow">Your sound</div>', unsafe_allow_html=True)

    saved_genre = (
        st.session_state.preferences["genre"]
    )

    genre = st.selectbox(
        "Preferred genre",
        GENRES,
        index=(
            GENRES.index(saved_genre)
            if saved_genre in GENRES
            else 0
        ),
    )

    saved_language = st.session_state.preferences.get("language", "Any")
    language = st.selectbox(
        "Song language",
        LANGUAGES,
        index=LANGUAGES.index(saved_language) if saved_language in LANGUAGES else 0,
        help="Filters mood recommendations to a curated set of songs in this language.",
    )

    search = st.text_input(
        "Search music",
        placeholder="Artist, song, or vibe...",
    )

    limit = st.slider(
        "Songs to discover",
        3,
        30,
        5,
    )

    if (
        mode != saved_mode
        or genre != saved_genre
        or language != saved_language
    ):
        st.session_state.preferences["mode"] = mode
        st.session_state.preferences["genre"] = genre
        st.session_state.preferences["language"] = language

        save_preferences(
            st.session_state.preferences
        )

    st.divider()

    st.markdown('<div class="sidebar-eyebrow">Playback</div>', unsafe_allow_html=True)

    try:
        devices = spotify.devices().get("devices", [])
        available = [
            device for device in devices
            if device.get("id") and not device.get("is_restricted")
        ]
        if available:
            device_by_id = {device["id"]: device for device in available}
            device_ids = list(device_by_id)
            active_id = next(
                (device["id"] for device in available if device.get("is_active")),
                None,
            )
            preferred_id = st.session_state.selected_device_id
            default_id = preferred_id if preferred_id in device_by_id else active_id
            if default_id is None:
                default_id = device_ids[0]
            selected_id = st.selectbox(
                "Choose playback device",
                device_ids,
                index=device_ids.index(default_id),
                format_func=lambda device_id: (
                    f"{device_by_id[device_id].get('name', 'Spotify')} "
                    f"({device_by_id[device_id].get('type', 'device')})"
                    + (" · Active" if device_by_id[device_id].get("is_active") else "")
                ),
            )
            st.session_state.selected_device_id = selected_id
            st.session_state.browser_playback = False
            st.markdown(
                '<div class="connection-pill">'
                + ('Playing on ' if selected_id == active_id else 'Ready to play on ')
                + escape(device_by_id[selected_id].get('name') or 'Spotify')
                + '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.session_state.selected_device_id = None
            st.session_state.browser_playback = True
            st.caption(
                "No Spotify Connect device is available. Use the player "
                "on a song card to listen in this browser."
            )

    except Exception:
        st.session_state.selected_device_id = None
        st.session_state.browser_playback = True
        st.caption(
            "Spotify device status unavailable. Browser playback is available."
        )

    st.button("↻ Refresh devices", key="refresh_spotify_devices", use_container_width=True)


# ==================================================
# HEADER
# ==================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-content">
            <div class="hero-label">✦ A MORE PERSONAL WAY TO LISTEN</div>
            <div class="hero-title">Feel it.<br>Find your sound.</div>
            <div class="hero-subtitle">
                Music that moves with your mood, your language,
                and the songs you love.
            </div>
            <div class="hero-highlights">
                <span>✧ Live mood tracking</span>
                <span>♫ Seven song languages</span>
                <span>◈ Spotify playback</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.playback_error:
    st.error(
        st.session_state.playback_error
    )

if st.session_state.playback_message:
    st.success(
        st.session_state.playback_message
    )

browser_track = st.session_state.browser_track
if browser_track:
    match = re.fullmatch(r"spotify:track:([A-Za-z0-9]{22})", browser_track.get("uri", ""))
    if match:
        web_url = f"https://open.spotify.com/track/{match.group(1)}"
        st.markdown(f"#### 🎧 Play in this browser: {browser_track.get('title', 'Song')}")
        st.components.v1.iframe(
            f"https://open.spotify.com/embed/track/{match.group(1)}",
            height=152,
            scrolling=False,
        )
        st.caption(
            "Press Play in the Spotify player above. Sign in to Spotify in "
            "this browser if it offers only a preview."
        )
        st.link_button("Open Spotify Web Player", web_url)
    else:
        st.warning("This track cannot be opened in the browser player.")
    if st.button("Close browser player"):
        st.session_state.browser_track = None
        st.rerun()


# ==================================================
# CAMERA
# ==================================================

camera = None

if navigation in [
    "Discover",
    "Mood Studio",
]:
    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">01 / MOOD INPUT</span>'
        '<h2>Read the moment</h2>'
        '<p>Use your camera or choose a mood yourself.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    camera_col, info_col = st.columns([2, 3])

    with camera_col:
        camera = webrtc_streamer(
            key="emotion-camera",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            video_processor_factory=EmotionVideoProcessor,
            media_stream_constraints={
                "video": True,
                "audio": False,
            },
            async_processing=True,
        )

    with info_col:
        st.markdown(
            '<div class="info-panel">'
            '<span class="eyebrow">✦ LIVE MOOD STUDIO</span>'
            '<h3>Your expression, a starting point.</h3>'
            '<p>Turn on the camera for a steady expression estimate. '
            'Your recommendations update as the reading settles.</p>'
            '<small>Feel different from the camera reading? Switch off '
            'Automatic detection and pick your mood in the sidebar.</small>'
            '</div>',
            unsafe_allow_html=True,
        )


# ==================================================
# LIVE MOOD AND DISCOVERY
# ==================================================

@st.fragment(run_every="2s")
def mood_and_discovery(spotify):
    detected = None
    confidence = 0.0
    camera_status = "Camera inactive"

    if (
        camera is not None
        and camera.state.playing
        and camera.video_processor is not None
    ):
        processor = camera.video_processor

        snapshot = processor.tracker.snapshot()
        status_info = processor.get_status()

        detected = snapshot.emotion
        confidence = snapshot.confidence
        camera_status = status_info["status"]

        if status_info["error"]:
            st.warning(
                "Emotion detection error: "
                + status_info["error"]
            )

        if (
            detected in MOOD_QUERIES
            and st.session_state.auto_mood
        ):
            st.session_state.mood = detected

    mood = st.session_state.mood

    first, second, third = st.columns(3)

    first.metric(
        "Recommended mood",
        f"{MOOD_EMOJIS[mood]} {mood.title()}",
    )

    second.metric(
        "Detected expression",
        (
            detected.title()
            if detected
            else "Waiting"
        ),
    )

    third.metric(
        "Model confidence",
        (
            f"{confidence:.1f}%"
            if detected
            else "—"
        ),
    )

    st.caption(
        f"Camera status: {camera_status}"
    )

    if (
        st.session_state.auto_mood
        and detected is None
    ):
        st.info(
            "Waiting for a stable facial expression. "
            "Until then, recommendations use your "
            "previously selected mood."
        )

    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">02 / YOUR MIX</span>'
        '<h2>Made for this moment</h2>'
        '<p>Explore songs tuned to your current mood and choices.</p>'
        '</div>'
        '<div class="filter-row">'
        f'<span class="filter-pill"><b>Mode</b> {escape(mode)}</span>'
        f'<span class="filter-pill"><b>Genre</b> {escape(genre)}</span>'
        f'<span class="filter-pill"><b>Language</b> {escape(language)}</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if limit > 5 and language == "Any":
        st.caption(
            "The first picks are curated for the mood; "
            "larger sets also include broader Spotify discoveries."
        )

    if search.strip():
        st.caption(
            "Search is active. With a song language selected, search filters "
            "the curated picks. Clear it to see all mood recommendations."
        )

    if language != "Any":
        st.caption(
            "Language picks come from a curated catalog. Spotify availability "
            "and genre filters may leave fewer songs than requested."
        )

    try:
        tracks = discover_tracks(
            mood,
            mode,
            genre,
            language,
            search,
            limit,
        )

        show_tracks(
            tracks,
            "discovery",
            spotify,
        )

    except Exception as error:
        st.error(
            f"Discovery error: {error}"
        )


# ==================================================
# PAGES
# ==================================================

if navigation == "Discover":
    mood_and_discovery(spotify)

    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">03 / PLAYBACK</span>'
        '<h2>On your speakers</h2>'
        '<p>Control the song playing on your active Spotify device.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    live_player(spotify)


elif navigation == "Mood Studio":
    mood_and_discovery(spotify)


elif navigation == "Favorites":
    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">YOUR COLLECTION</span>'
        '<h2>Saved for another listen</h2>'
        '<p>The songs you keep close, all in one place.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    favorites = list(
        st.session_state.preferences[
            "favorites"
        ].values()
    )

    show_tracks(
        favorites,
        "favorites",
        spotify,
    )

    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">PLAYBACK</span>'
        '<h2>On your speakers</h2>'
        '</div>',
        unsafe_allow_html=True,
    )

    live_player(spotify)


elif navigation == "Listening Insights":
    st.markdown(
        '<div class="section-heading">'
        '<span class="eyebrow">YOUR LISTENING STORY</span>'
        '<h2>What moves you</h2>'
        '<p>A closer look at the sounds you choose and save.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    insights = get_insights(
        st.session_state.preferences
    )

    a, b, c = st.columns(3)

    a.metric(
        "Songs selected",
        insights["plays"],
    )

    b.metric(
        "Favorites",
        insights["favorites"],
    )

    c.metric(
        "Disliked songs",
        insights["dislikes"],
    )

    st.markdown(
        "### 🎭 Mood Distribution"
    )

    if insights["moods"]:
        st.bar_chart(
            insights["moods"]
        )
    else:
        st.info(
            "Play songs to generate mood insights."
        )

    st.markdown(
        "### 🎤 Most Selected Artists"
    )

    if insights["artists"]:
        for artist, count in insights["artists"]:
            st.write(
                f"**{artist}** — "
                f"{count} selections"
            )
    else:
        st.caption(
            "No listening history yet."
        )

    st.markdown(
        "### 🕘 Recently Selected"
    )

    recent = [
        event["track"]
        for event in (
            st.session_state.preferences[
                "history"
            ][:9]
        )
    ]

    show_tracks(
        recent,
        "recent",
        spotify,
    )

    st.markdown(
        "### 🎮 Spotify Live Player"
    )

    live_player(spotify)


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Emotion Music 3.0 | "
    "DeepFace + Streamlit + Spotify + "
    "Personalized Recommendations"
)

