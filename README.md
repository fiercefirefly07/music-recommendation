# Emotion Music 3.0

A local Streamlit app with a black and electric blue interface and the familiar controls: Discover, Mood Studio, Favorites, Listening Insights, automatic or manual mood, Match/Improve modes, genre, search, track count, favorites/dislikes, and Spotify player controls. Webcam readings are held through brief face-detection gaps.

The **Song language** selector in the original sidebar supports Any, English,
Hindi, Tamil, Telugu, Malayalam, Kannada, and Punjabi. It is saved in
`user_preferences.json` alongside genre and recommendation mode. With a
specific language selected, the app uses mood-aware editorial song pools and
shows only exact Spotify title/artist matches. Search then filters those
curated picks by title or artist. **Any** keeps the original broad Spotify
discovery behavior. Spotify does not expose a track-language field, so the
catalog is maintained in `language_catalog.py`; some songs may be unavailable
in a particular Spotify region.

- **Match:** stay with the expression's musical energy.
- **Improve:** move gently toward calmer or brighter energy.

Facial expressions are only clues. Turn off **Automatic detection** and select **Your mood** whenever the camera reading does not reflect how you feel.

## Setup (Windows PowerShell)

Use Python **3.11 or 3.12**. The existing `C:\EmotionMusicRecommendation\.venv` may be used if its dependencies are present. Otherwise, in this folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The existing project may already have `.streamlit/secrets.toml` with `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI`. Keep that file in place. If it is missing, copy `.env.example` to `.env` and fill in those three settings. The app reads either file, with `secrets.toml` taking precedence. Keep credentials private.

Set the redirect URI in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) to exactly the value in your settings file. The local example is `http://127.0.0.1:8501`.

The app uses the existing `.spotify_cache` and the same OAuth scopes as the old app. A reconnect should only be necessary if the token has become invalid.

The app reads **`user_preferences.json`** in this folder if it exists. It preserves the original `favorites` dictionary, `history` events, dislikes, genre, mode, and other top-level settings, and saves changes atomically. If the file has not been created yet, it will be created when you save a favorite or play a track. Legacy favorite entries without Spotify track and album URIs remain visible; playback of those entries requires resolving them to Spotify album tracks.

```powershell
streamlit run app.py
```

Open `http://127.0.0.1:8501`. Allow camera access and connect Spotify. On a **Premium** account, select an available Spotify Connect device in the sidebar and click Play on a song card. The app can activate a listed device even when it is paused. If no device is available, each song card shows Spotify's in-page player. Click Play there once to start the song. The original Discover and Mood Studio views appear with their original controls.

The first DeepFace run downloads its model weights and can take a minute. The camera uses a public Google STUN server for WebRTC discovery. A remotely hosted app also requires HTTPS and may require a TURN server on restrictive networks.

## What is in each file

| File | Purpose |
| --- | --- |
| `app.py` | Original multi-page Streamlit UI and controls, with improved camera and discovery logic |
| `emotion_tracker.py` | Background detection, face-box smoothing, emotion smoothing, short-gap hold |
| `assets/haarcascade_frontalface_default.xml` | Bundled OpenCV face detector data; works even when OpenCV omits its data folder |
| `music.py` | Editorial Match/Improve catalog, genre tags, and exact Spotify track lookup |
| `browser_player.py` | Native Spotify player shown directly on each song card |
| `.streamlit/config.toml` | Dark widget and page theme; separate from Spotify secrets |
| `assets/theme.css` | Electric blue styles for cards, controls, sidebar, and player |
| `language_catalog.py` | Mood-aware song pools for seven vocal languages |
| `recommendation_engine.py` | Existing favorites, dislikes, history, insights, and personalized ranking |

Spotify playback deliberately calls:

```python
spotify.start_playback(context_uri=album_uri, offset={"uri": track_uri})
```

It does not pass `device_id` or `uris` to `start_playback`. If the chosen device is available but inactive, the app first transfers playback to it. When no device is available, Spotify's native player appears on each song card. The click goes straight to Spotify's player and avoids the extra Streamlit round trip that made the old browser fallback require two clicks. Editorial song resolution is cached for 24 hours by title and artist across token refreshes, so switching moods does not repeat the same searches. The first five default picks come from the curated mood catalog. Asking for more tracks adds broader Spotify search results, which may fit the mood less precisely. A manual search follows the search text you enter. This does not rely on the unavailable recommendations endpoint.

## Troubleshooting

- **Face appears and disappears:** use front lighting, keep your face large in the frame, and close other apps using the webcam. The tracker holds a recent reading for up to 4 seconds. The manual mood control remains available.
- **Face detector could not load:** check that `assets/haarcascade_frontalface_default.xml` exists beside the app. This update bundles that detector because some OpenCV installs omit it.
- **Camera never starts:** allow browser camera access and use the local `127.0.0.1` address. A remote address must use HTTPS.
- **Spotify connection fails:** check that the redirect URI matches exactly, that the account can access your developer app, and that the token cache is writable.
- **Playback fails:** choose a listed device in the sidebar and click **Refresh devices** if you just opened Spotify. You do not need to start a song there first. If no device appears, try the in-page Spotify player and sign in to Spotify in the same browser. Spotify may limit an Embed to a preview if encrypted-media playback is unavailable.
- **Some tracks are missing:** availability varies by country. The app only returns exact artist/title matches with album playback context.

## Source references

- [streamlit-webrtc usage and callback threading](https://github.com/whitphx/streamlit-webrtc/blob/main/README.md)
- [DeepFace facial attribute analysis](https://github.com/serengil/deepface/blob/master/README.md)
- [OpenCV frontal-face cascade source and included license](https://github.com/opencv/opencv/blob/4.x/data/haarcascades/haarcascade_frontalface_default.xml)
- [Spotify search](https://developer.spotify.com/documentation/web-api/reference/search)
- [Spotify start/resume playback](https://developer.spotify.com/documentation/web-api/reference/start-a-users-playback)
- [Spotify February 2026 developer-mode changes](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)
