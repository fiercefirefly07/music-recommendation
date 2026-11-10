
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Emotion Music | Spotify Player",
    page_icon="🎵",
    layout="wide"
)

# =====================================================
# CUSTOM STYLING
# =====================================================

st.markdown("""
<style>
.stApp {
    background: #101114;
    color: white;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

h1, h2, h3 {
    color: white !important;
}

div.stButton > button {
    border-radius: 12px;
    min-height: 45px;
}

div.stButton > button[kind="primary"] {
    background: #1DB954;
    color: #000;
    border: none;
    font-weight: 700;
}

div.stButton > button[kind="primary"]:hover {
    background: #1ed760;
    color: #000;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================

def format_duration(milliseconds):
    seconds = max(0, int(milliseconds or 0) // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def spotify_error_message(error):
    if isinstance(error, SpotifyException):
        status = error.http_status

        if status == 403:
            return (
                "Spotify returned 403 Forbidden. "
                "Your developer app may not have access to "
                "this playback endpoint, even with Premium."
            )

        if status == 404:
            return (
                "Spotify returned 404. No suitable active "
                "playback device was found."
            )

        if status == 401:
            return (
                "Spotify returned 401. Your session may have "
                "expired or the required permissions are missing."
            )

        return f"Spotify API error {status}: {error.msg}"

    return str(error)


def run_command(action, success_message):
    try:
        action()
        st.success(success_message)
    except Exception as error:
        st.error(spotify_error_message(error))


# =====================================================
# HEADER
# =====================================================

st.title("🎵 Emotion Music 2.0")
st.caption("Spotify Premium Integration & Playback Test")

st.divider()

# =====================================================
# SPOTIFY AUTHENTICATION
# =====================================================

try:
    auth_manager = SpotifyOAuth(
        client_id=st.secrets["SPOTIFY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
        scope=(
            "user-read-private "
            "user-read-email "
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-read-currently-playing"
        ),
        open_browser=False,
        cache_path=".spotify_cache"
    )

    oauth_error = st.query_params.get("error")
    code = st.query_params.get("code")

    if oauth_error:
        st.error(f"Spotify authorization failed: {oauth_error}")
        st.stop()

    if code:
        token_info = auth_manager.get_access_token(
            code,
            check_cache=False
        )

        st.session_state["spotify_token"] = token_info
        st.query_params.clear()
        st.rerun()

    token_info = st.session_state.get("spotify_token")

    if token_info:
        if auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(
                token_info["refresh_token"]
            )
            st.session_state["spotify_token"] = token_info

    if not token_info:
        token_info = auth_manager.get_cached_token()

    if not token_info:
        st.info("Connect your Spotify account to continue.")

        st.link_button(
            "🎧 Login with Spotify",
            auth_manager.get_authorize_url(),
            use_container_width=True
        )

        st.stop()

    spotify = spotipy.Spotify(
        auth=token_info["access_token"],
        requests_timeout=10,
        retries=1
    )

    # =================================================
    # ACCOUNT INFORMATION
    # =================================================

    profile = spotify.current_user()

    st.success("Spotify authentication successful!")

    a, b, c = st.columns(3)

    with a:
        st.metric(
            "Account",
            profile.get("display_name") or "Spotify User"
        )

    with b:
        st.metric(
            "Subscription",
            str(profile.get("product", "Unknown")).title()
        )

    with c:
        st.metric(
            "Country",
            profile.get("country", "Unknown")
        )

    st.divider()

    # =================================================
    # PLAYBACK DEVICE SELECTION
    # =================================================

    st.subheader("💻 Spotify Playback Devices")

    if st.button("🔄 Refresh Devices"):
        st.rerun()

    devices_response = spotify.devices()
    devices = devices_response.get("devices", [])

    if not devices:
        st.warning(
            "No playback devices found. Open the Spotify "
            "desktop app and start playing a song."
        )
        selected_device_id = None

    else:
        device_names = {
            device["id"]: (
                f"{device['name']} "
                f"({device['type']})"
                + (" • Active" if device.get("is_active") else "")
            )
            for device in devices
            if device.get("id")
        }

        if not device_names:
            selected_device_id = None
            st.warning("No controllable device IDs were returned.")

        else:
            device_ids = list(device_names.keys())

            active_id = next(
                (
                    device["id"]
                    for device in devices
                    if device.get("is_active")
                    and device.get("id") in device_names
                ),
                device_ids[0]
            )

            selected_device_id = st.selectbox(
                "Choose playback device",
                options=device_ids,
                index=device_ids.index(active_id),
                format_func=lambda device_id: device_names[device_id]
            )

    st.divider()

    # =================================================
    # CURRENTLY PLAYING
    # =================================================

    st.subheader("🎶 Currently Playing")

    if st.button("🔄 Refresh Current Track"):
        st.rerun()

    current = None

    try:
        current = spotify.current_playback()
    except Exception as error:
        st.warning(spotify_error_message(error))

    if current and current.get("item"):

        track = current["item"]

        left, right = st.columns([1, 3])

        with left:
            images = track.get("album", {}).get("images", [])

            if images:
                st.image(images[0]["url"], width=200)

        with right:
            st.markdown(
                f"### {track.get('name', 'Unknown Track')}"
            )

            artists = ", ".join(
                artist.get("name", "")
                for artist in track.get("artists", [])
            )

            st.write(f"**Artist:** {artists}")

            st.write(
                "**Album:**",
                track.get("album", {}).get("name", "Unknown")
            )

            st.write(
                "**Status:**",
                "▶ Playing"
                if current.get("is_playing")
                else "⏸ Paused"
            )

            progress = current.get("progress_ms") or 0
            duration = track.get("duration_ms") or 0

            st.write(
                f"{format_duration(progress)} / "
                f"{format_duration(duration)}"
            )

            if duration > 0:
                st.progress(
                    min(1.0, max(0.0, progress / duration))
                )

    else:
        st.info(
            "No active track was returned. "
            "Play a song in the Spotify desktop app."
        )

    st.divider()

    # =================================================
    # PLAYBACK CONTROLS
    # =================================================

    st.subheader("🎮 Spotify Player Controls")

    if selected_device_id:

        previous_col, play_col, pause_col, next_col = st.columns(4)

        with previous_col:
            if st.button(
                "⏮ Previous",
                use_container_width=True
            ):
                run_command(
                    lambda: spotify.previous_track(
                        device_id=selected_device_id
                    ),
                    "Previous command sent!"
                )

        with play_col:
            if st.button(
                "▶ Play",
                type="primary",
                use_container_width=True
            ):
                run_command(
                    lambda: spotify.start_playback(
                        device_id=selected_device_id
                    ),
                    "Play command sent!"
                )

        with pause_col:
            if st.button(
                "⏸ Pause",
                use_container_width=True
            ):
                run_command(
                    lambda: spotify.pause_playback(
                        device_id=selected_device_id
                    ),
                    "Pause command sent!"
                )

        with next_col:
            if st.button(
                "⏭ Next",
                use_container_width=True
            ):
                run_command(
                    lambda: spotify.next_track(
                        device_id=selected_device_id
                    ),
                    "Next command sent!"
                )

        st.divider()

        # =============================================
        # VOLUME CONTROL
        # =============================================

        st.subheader("🔊 Volume Control")

        current_volume = next(
            (
                device.get("volume_percent")
                for device in devices
                if device.get("id") == selected_device_id
            ),
            None
        )

        volume = st.slider(
            "Volume",
            min_value=0,
            max_value=100,
            value=(
                int(current_volume)
                if current_volume is not None
                else 50
            ),
            step=5
        )

        if st.button("Apply Volume"):
            run_command(
                lambda: spotify.volume(
                    volume_percent=volume,
                    device_id=selected_device_id
                ),
                f"Volume command sent: {volume}%"
            )

        # =============================================
        # SEEK CONTROL
        # =============================================

        if (
            current
            and current.get("item")
            and current.get("device", {}).get("id")
            == selected_device_id
        ):
            st.divider()
            st.subheader("⏩ Seek")

            duration_ms = (
                current["item"].get("duration_ms") or 0
            )

            if duration_ms > 0:
                seek_seconds = st.slider(
                    "Seek to (seconds)",
                    min_value=0,
                    max_value=duration_ms // 1000,
                    value=min(
                        (current.get("progress_ms") or 0) // 1000,
                        duration_ms // 1000
                    )
                )

                if st.button("Seek to Position"):
                    run_command(
                        lambda: spotify.seek_track(
                            position_ms=seek_seconds * 1000,
                            device_id=selected_device_id
                        ),
                        "Seek command sent!"
                    )

    else:
        st.info(
            "Select an available Spotify playback device "
            "to enable the controls."
        )

    st.divider()

    st.caption(
        "Emotion Music 2.0 • Spotify API Playback Test"
    )

except Exception as error:
    st.error(spotify_error_message(error))
