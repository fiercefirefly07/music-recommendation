
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Spotify Playback Fix Test",
    page_icon="🎧",
    layout="centered",
)

st.title("🎧 Spotify Playback Fix")
st.caption("Testing album-context playback instead of direct track URI playback.")

# ==========================================================
# SPOTIFY AUTHENTICATION
# ==========================================================

try:
    auth = SpotifyOAuth(
        client_id=st.secrets["SPOTIFY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
        scope=(
            "user-read-private "
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-read-currently-playing"
        ),
        cache_path=".spotify_cache",
    )

    token = auth.get_cached_token()

    if not token:
        st.error(
            "Spotify login not found. "
            "Log in through your main app first."
        )
        st.stop()

    spotify = spotipy.Spotify(
        auth_manager=auth,
        requests_timeout=10,
        retries=1,
    )

except Exception as error:
    st.error(f"Spotify connection error: {error}")
    st.stop()


# ==========================================================
# GET CURRENT SONG
# ==========================================================

try:
    playback = spotify.current_playback()

    if not playback or not playback.get("item"):
        st.warning(
            "Open Spotify desktop, play any song, "
            "then click Refresh."
        )

        if st.button("🔄 Refresh"):
            st.rerun()

        st.stop()

    track = playback["item"]
    album = track.get("album") or {}
    device = playback.get("device") or {}

    track_name = track.get("name", "Unknown")
    track_uri = track.get("uri")
    album_name = album.get("name", "Unknown")
    album_uri = album.get("uri")
    device_name = device.get("name", "Unknown")

    artists = ", ".join(
        artist.get("name", "")
        for artist in track.get("artists", [])
    )

    images = album.get("images") or []

    if images:
        st.image(
            images[0]["url"],
            width=250,
        )

    st.subheader(track_name)
    st.write(f"**Artist:** {artists}")
    st.write(f"**Album:** {album_name}")
    st.write(f"**Device:** {device_name}")

    st.write(
        "**Playback status:**",
        "▶ Playing" if playback.get("is_playing") else "⏸ Paused",
    )

    with st.expander("Track Information"):
        st.code(track_uri or "Unavailable")
        st.code(album_uri or "Unavailable")

except Exception as error:
    st.error(f"Unable to get playback: {error}")
    st.stop()


# ==========================================================
# ALBUM-CONTEXT PLAYBACK WORKAROUND
# ==========================================================

st.divider()
st.subheader("🧪 Test Album-Context Playback")

st.info(
    "This sends Spotify the album URI and starts "
    "at the selected track, instead of sending "
    "the track URI alone."
)

if st.button(
    "▶ Play Using Album Context",
    type="primary",
    use_container_width=True,
):
    if not album_uri or not track_uri:
        st.error(
            "Album or track URI is missing. "
            "Try another song."
        )
    else:
        try:
            spotify.start_playback(
                context_uri=album_uri,
                offset={"uri": track_uri},
            )

            st.success(
                "Album-context playback command accepted."
            )

            st.info(
                "Check Spotify desktop to confirm "
                "the song actually plays with sound."
            )

        except SpotifyException as error:
            st.error(
                f"Spotify API error {error.http_status}: "
                f"{error.msg}"
            )

        except Exception as error:
            st.error(str(error))


# ==========================================================
# PLAYBACK CONTROLS
# ==========================================================

st.divider()
st.subheader("🎮 Playback Controls")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "▶ Resume",
        use_container_width=True,
    ):
        try:
            spotify.start_playback()
            st.success("Resume command sent.")
        except Exception as error:
            st.error(str(error))

with col2:
    if st.button(
        "⏸ Pause",
        use_container_width=True,
    ):
        try:
            spotify.pause_playback()
            st.success("Pause command sent.")
        except Exception as error:
            st.error(str(error))

with col3:
    if st.button(
        "⏭ Next",
        use_container_width=True,
    ):
        try:
            spotify.next_track()
            st.success("Next command sent.")
        except Exception as error:
            st.error(str(error))


# ==========================================================
# REFRESH
# ==========================================================

st.divider()

if st.button(
    "🔄 Refresh Current Song",
    use_container_width=True,
):
    st.rerun()

st.caption(
    "Spotify playback test | Album-context workaround"
)
