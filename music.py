"""Curated mood journeys resolved to playable Spotify album tracks."""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

from language_catalog import LANGUAGES, MOOD_GROUPS, SONGS


@dataclass(frozen=True)
class Seed:
    title: str
    artist: str
    why: str
    language: str = "English"
    genres: tuple[str, ...] = ()


def s(title: str, artist: str, why: str) -> Seed:
    return Seed(title, artist, why)


# Match reflects the expression. Improve gently changes the listening energy.
# These are editorial choices, not a claim that a facial expression reveals feelings.
CATALOG: dict[str, dict[str, list[Seed]]] = {
    "happy": {
        "Match": [
            s("Good as Hell", "Lizzo", "Bold, upbeat confidence"),
            s("Levitating", "Dua Lipa", "Bright dance pop"),
            s("September", "Earth, Wind & Fire", "Classic celebration"),
            s("Walking on Sunshine", "Katrina and the Waves", "Instant lift"),
            s("Happy", "Pharrell Williams", "Pure sunny energy"),
        ],
        "Improve": [
            s("Sunset Lover", "Petit Biscuit", "A gentle comedown"),
            s("Golden", "Harry Styles", "Warm and buoyant"),
            s("Put Your Records On", "Corinne Bailey Rae", "Relaxed optimism"),
            s("Here Comes the Sun", "The Beatles", "Soft sunshine"),
            s("Sunday Best", "Surfaces", "Easy good vibes"),
        ],
    },
    "sad": {
        "Match": [
            s("Someone Like You", "Adele", "Room for reflection"),
            s("The Night We Met", "Lord Huron", "Tender melancholy"),
            s("Skinny Love", "Bon Iver", "Quiet vulnerability"),
            s("Liability", "Lorde", "Intimate and honest"),
            s("Fix You", "Coldplay", "A gentle build"),
        ],
        "Improve": [
            s("Three Little Birds", "Bob Marley & The Wailers", "Steady reassurance"),
            s("Dog Days Are Over", "Florence + The Machine", "A gradual release"),
            s("Unwritten", "Natasha Bedingfield", "Open possibilities"),
            s("Lovely Day", "Bill Withers", "Warm encouragement"),
            s("Brave", "Sara Bareilles", "Quiet resolve"),
        ],
    },
    "angry": {
        "Match": [
            s("Killing In The Name", "Rage Against The Machine", "Raw intensity"),
            s("Uprising", "Muse", "Defiant momentum"),
            s("Misery Business", "Paramore", "High energy release"),
            s("Seven Nation Army", "The White Stripes", "Driving rock pulse"),
            s("bad guy", "Billie Eilish", "Sharp, controlled edge"),
        ],
        "Improve": [
            s("Weightless", "Marconi Union", "Spacious ambient calm"),
            s("Holocene", "Bon Iver", "A slower perspective"),
            s("Breathe Me", "Sia", "A quiet reset"),
            s("Sunset Lover", "Petit Biscuit", "Soft electronic glow"),
            s("River", "Leon Bridges", "Grounded soul"),
        ],
    },
    "fear": {
        "Match": [
            s("Breathe Me", "Sia", "Gentle vulnerability"),
            s("The Scientist", "Coldplay", "Soft contemplation"),
            s("Youth", "Daughter", "Hushed atmosphere"),
            s("To Build A Home", "The Cinematic Orchestra", "Emotional space"),
            s("Holocene", "Bon Iver", "Quiet reflection"),
        ],
        "Improve": [
            s("Weightless", "Marconi Union", "Unhurried ambient sound"),
            s("Three Little Birds", "Bob Marley & The Wailers", "Reassuring rhythm"),
            s("Here Comes the Sun", "The Beatles", "Gentle optimism"),
            s("Bloom", "The Paper Kites", "Soft, steady warmth"),
            s("Better Together", "Jack Johnson", "Comforting acoustic sound"),
        ],
    },
    "disgust": {
        "Match": [
            s("bad guy", "Billie Eilish", "Wry dark pop"),
            s("Take Me Out", "Franz Ferdinand", "Crisp indie edge"),
            s("Feel Good Inc.", "Gorillaz", "Sardonic groove"),
            s("Uprising", "Muse", "A defiant push"),
            s("Seven Nation Army", "The White Stripes", "Focused guitar drive"),
        ],
        "Improve": [
            s("Electric Feel", "MGMT", "Playful change of scene"),
            s("Put Your Records On", "Corinne Bailey Rae", "Easy reset"),
            s("Lovely Day", "Bill Withers", "Warm soul"),
            s("Sunday Best", "Surfaces", "Fresh perspective"),
            s("Golden", "Harry Styles", "Bright forward motion"),
        ],
    },
    "surprise": {
        "Match": [
            s("Midnight City", "M83", "A cinematic rush"),
            s("Electric Feel", "MGMT", "Colorful discovery"),
            s("Tongue Tied", "Grouplove", "Bursting indie pop"),
            s("Feel It Still", "Portugal. The Man", "Bouncy surprise"),
            s("On Top Of The World", "Imagine Dragons", "Big open energy"),
        ],
        "Improve": [
            s("A Sky Full of Stars", "Coldplay", "Joyful release"),
            s("Riptide", "Vance Joy", "Playful and easy"),
            s("Sunset Lover", "Petit Biscuit", "A smoother landing"),
            s("Dreams", "Fleetwood Mac", "Airy classic"),
            s("Golden", "Harry Styles", "Warm momentum"),
        ],
    },
    "neutral": {
        "Match": [
            s("Dreams", "Fleetwood Mac", "Easy, familiar flow"),
            s("Better Together", "Jack Johnson", "Comfortable acoustic pace"),
            s("Come Away With Me", "Norah Jones", "Low-key warmth"),
            s("Sunset Lover", "Petit Biscuit", "Soft instrumental color"),
            s("Bloom", "The Paper Kites", "Gentle indie sound"),
        ],
        "Improve": [
            s("Feel It Still", "Portugal. The Man", "A little extra bounce"),
            s("Sunday Best", "Surfaces", "Light optimism"),
            s("Levitating", "Dua Lipa", "Dance floor energy"),
            s("Good as Hell", "Lizzo", "Confidence boost"),
            s("Walking on Sunshine", "Katrina and the Waves", "A bright turn"),
        ],
    },
}


# Editorial genre tags are used only for the user's genre filter. Spotify's
# track response does not provide a reliable per-track genre field.
ARTIST_GENRES = {
    "Lizzo": {"Pop", "Hip-Hop"}, "Dua Lipa": {"Pop", "Dance"},
    "Earth, Wind & Fire": {"Dance"}, "Katrina and the Waves": {"Rock", "Pop"},
    "Pharrell Williams": {"Pop", "Hip-Hop"}, "Petit Biscuit": {"Electronic", "Ambient", "Instrumental"},
    "Harry Styles": {"Pop"}, "Corinne Bailey Rae": {"Pop", "Acoustic"},
    "The Beatles": {"Rock", "Pop", "Acoustic"}, "Surfaces": {"Pop", "Hip-Hop"},
    "Adele": {"Pop", "Acoustic"}, "Lord Huron": {"Indie", "Acoustic"},
    "Bon Iver": {"Indie", "Acoustic"}, "Lorde": {"Pop", "Indie"},
    "Coldplay": {"Pop", "Rock"}, "Bob Marley & The Wailers": {"Pop"},
    "Florence + The Machine": {"Indie", "Rock", "Pop"},
    "Natasha Bedingfield": {"Pop"}, "Bill Withers": {"Pop"},
    "Sara Bareilles": {"Pop", "Acoustic"},
    "Rage Against The Machine": {"Rock"}, "Muse": {"Rock"},
    "Paramore": {"Rock", "Pop"}, "The White Stripes": {"Rock"},
    "Billie Eilish": {"Pop", "Electronic"}, "Marconi Union": {"Ambient", "Instrumental", "Electronic"},
    "Sia": {"Pop"}, "Leon Bridges": {"Pop"}, "Daughter": {"Indie", "Acoustic"},
    "The Cinematic Orchestra": {"Ambient", "Instrumental"},
    "The Paper Kites": {"Indie", "Acoustic"}, "Jack Johnson": {"Acoustic", "Pop"},
    "Franz Ferdinand": {"Indie", "Rock"}, "Gorillaz": {"Hip-Hop", "Electronic"},
    "MGMT": {"Indie", "Electronic"}, "M83": {"Electronic", "Ambient"},
    "Grouplove": {"Indie", "Rock"}, "Portugal. The Man": {"Indie", "Rock"},
    "Imagine Dragons": {"Rock", "Pop"}, "Vance Joy": {"Indie", "Acoustic"},
    "Fleetwood Mac": {"Rock", "Pop"}, "Norah Jones": {"Acoustic", "Pop"},
}


def matches_genre(track: dict, genre: str) -> bool:
    if genre == "Any":
        return True
    return genre in track.get("seed_genres", ()) or genre in ARTIST_GENRES.get(
        track.get("seed_artist", ""), set()
    )


def _normal(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _resolve(spotify, seed: Seed):
    query = f'track:"{seed.title}" artist:"{seed.artist}"'
    target_title = _normal(seed.title)
    target_artist = _normal(seed.artist)
    # A title-only fallback handles soundtrack listings whose Spotify artist
    # credits differ from the featured singer. Artist matching remains required.
    for search_query in (query, f'track:"{seed.title}"'):
        items = spotify.search(q=search_query, type="track", limit=10).get(
            "tracks", {}
        ).get("items", [])
        for track in items:
            album = track.get("album") or {}
            artists = track.get("artists") or []
            title = _normal(track.get("name", ""))
            artist_names = [_normal(artist.get("name", "")) for artist in artists]
            if (title == target_title or title.startswith(target_title + " ")) and any(
                name == target_artist or target_artist in name for name in artist_names
            ) and track.get("uri") and album.get("uri") and track.get("is_playable", True):
                return {
                    "id": track["uri"],
                    "uri": track["uri"],
                    "album_uri": album["uri"],
                    "title": track["name"],
                    "artist": ", ".join(a.get("name", "") for a in artists),
                    "artists": [a.get("name", "") for a in artists],
                    "album": album.get("name", ""),
                    "image": (album.get("images") or [{}])[0].get("url"),
                    "url": (track.get("external_urls") or {}).get("spotify", ""),
                    "reason": seed.why,
                    "seed_artist": seed.artist,
                    "language": seed.language,
                    "seed_genres": seed.genres,
                }
    return None


def recommend(spotify, mood: str, mode: str, count: int = 5,
              shuffle: bool = False, excluded_uris=(), language: str = "Any",
              resolver=None):
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported song language: {language}")
    if language in ("Any", "English"):
        seeds = list(CATALOG[mood][mode])
        if language == "English":
            # These are instrumentals, so they cannot meet a vocal-language choice.
            seeds = [seed for seed in seeds if seed.artist not in
                     {"Marconi Union", "Petit Biscuit", "The Cinematic Orchestra"}]
    else:
        seeds = [
            Seed(title, artist, why, language, genres)
            for group in MOOD_GROUPS[mood][mode]
            for title, artist, why, genres in SONGS[language][group]
        ]
    if shuffle:
        random.shuffle(seeds)
    tracks, seen = [], set(excluded_uris)
    for seed in seeds:
        track = resolver(seed) if resolver is not None else _resolve(spotify, seed)
        if track and track["uri"] not in seen:
            tracks.append(track)
            seen.add(track["uri"])
        if len(tracks) >= count:
            break
    return tracks
