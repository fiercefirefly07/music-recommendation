
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "user_preferences.json"

MOOD_QUERIES = {
    "happy": ["feel good pop", "upbeat dance", "happy hits"],
    "sad": ["sad acoustic", "emotional ballads", "soft indie"],
    "neutral": ["chill pop", "indie chill", "lofi music"],
    "angry": ["energetic rock", "intense workout", "alternative rock"],
    "fear": ["calming piano", "peaceful ambient", "relaxing instrumental"],
    "surprise": ["dance pop", "party hits", "upbeat music"],
    "disgust": ["calm acoustic", "relaxing indie", "peaceful music"],
}

IMPROVE_QUERIES = {
    "happy": ["happy dance", "feel good hits"],
    "sad": ["uplifting pop", "hopeful acoustic", "feel good music"],
    "neutral": ["upbeat indie", "fresh pop"],
    "angry": ["calming indie", "relaxing acoustic", "peaceful music"],
    "fear": ["comforting acoustic", "calming piano", "soft pop"],
    "surprise": ["chill pop", "feel good dance"],
    "disgust": ["relaxing indie", "positive acoustic"],
}


def default_preferences():
    return {
        "favorites": {},
        "dislikes": [],
        "history": [],
        "genre": "Any",
        "language": "Any",
        "mode": "Match My Mood",
    }


def load_preferences():
    if not DATA_FILE.exists():
        return default_preferences()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return default_preferences()

        defaults = default_preferences()

        for key, value in defaults.items():
            data.setdefault(key, value)

        return data

    except (OSError, json.JSONDecodeError):
        return default_preferences()


def save_preferences(data):
    temporary = DATA_FILE.with_suffix(".json.tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temporary.replace(DATA_FILE)


def toggle_favorite(data, track):
    track_id = track["id"]

    if track_id in data["favorites"]:
        del data["favorites"][track_id]
        liked = False
    else:
        data["favorites"][track_id] = track
        liked = True

        if track_id in data["dislikes"]:
            data["dislikes"].remove(track_id)

    save_preferences(data)
    return liked


def toggle_dislike(data, track):
    track_id = track["id"]

    if track_id in data["dislikes"]:
        data["dislikes"].remove(track_id)
        disliked = False
    else:
        data["dislikes"].append(track_id)
        data["favorites"].pop(track_id, None)
        disliked = True

    save_preferences(data)
    return disliked


def record_play(data, track, mood):
    event = {
        "track": track,
        "mood": mood,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    data["history"].insert(0, event)
    data["history"] = data["history"][:200]

    save_preferences(data)


def get_queries(mood, mode, genre="Any", search=""):
    if search.strip():
        return [search.strip()]

    mapping = (
        IMPROVE_QUERIES
        if mode == "Improve My Mood"
        else MOOD_QUERIES
    )

    queries = mapping.get(mood, MOOD_QUERIES["neutral"])

    if genre != "Any":
        return [f"{query} {genre}" for query in queries]

    return queries


def get_artist_weights(data):
    weights = Counter()

    for track in data["favorites"].values():
        for artist in track.get("artists", []):
            weights[artist.lower()] += 3

    for event in data["history"][:50]:
        track = event.get("track", {})

        for artist in track.get("artists", []):
            weights[artist.lower()] += 1

    return weights


def rank_tracks(tracks, data, mood, mode):
    artist_weights = get_artist_weights(data)

    favorite_ids = set(data["favorites"])
    dislike_ids = set(data["dislikes"])

    recent_ids = {
        event.get("track", {}).get("id")
        for event in data["history"][:15]
    }

    ranked = []

    for position, track in enumerate(tracks):
        track_id = track["id"]

        if track_id in dislike_ids:
            continue

        # Spotify search phrases provide approximate mood relevance.
        # Spotify does not supply a verified emotion label here.
        score = 50.0 - min(position, 30) * 0.6
        reasons = ["Matches your selected music discovery style"]

        if track_id in favorite_ids:
            score += 30
            reasons.append("You've saved this song")

        artist_score = sum(
            artist_weights.get(artist.lower(), 0)
            for artist in track.get("artists", [])
        )

        if artist_score:
            score += min(artist_score * 4, 24)
            reasons.append("Similar to artists you enjoy")

        if track_id in recent_ids:
            score -= 18
        else:
            score += 8
            reasons.append("A fresh discovery for you")

        if mode == "Improve My Mood":
            reasons[0] = "Selected to support a mood shift"

        result = dict(track)
        result["score"] = round(score, 1)
        result["reasons"] = reasons

        ranked.append(result)

    ranked.sort(key=lambda song: song["score"], reverse=True)
    return ranked


def get_insights(data):
    history = data["history"]

    moods = Counter(
        event.get("mood", "unknown")
        for event in history
    )

    artists = Counter()

    for event in history:
        for artist in event.get("track", {}).get("artists", []):
            artists[artist] += 1

    return {
        "plays": len(history),
        "favorites": len(data["favorites"]),
        "dislikes": len(data["dislikes"]),
        "moods": dict(moods),
        "artists": artists.most_common(5),
    }
