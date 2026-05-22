import streamlit as st
import requests
import random
import json
import os
from datetime import datetime

# Const
OMDB_API_KEY = "de9eff75"
BASE_URL = "http://www.omdbapi.com/"
FAVORITES_FILE = "favorites.json"

st.set_page_config(page_title="Movie Mood", page_icon="🎬", layout="centered")


# css style
st.markdown("""
<style>
/* Page background — warm cream */
.stApp { background-color: #f5e6d3; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: #fff8f0;
    border-radius: 10px;
    border: 1px solid #f0d9c0;
    color: #7a5c3a;
    font-weight: 500;
    padding: 6px 18px;
}
.stTabs [aria-selected="true"] {
    background: #f5e0c8 !important;
    color: #5a3a1a !important;
    border-color: #e0b88a !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid #e0b88a;
    background: #fff8f0;
    color: #7a5c3a;
    font-weight: 500;
    transition: background 0.15s;
}
.stButton > button:hover {
    background: #f5e0c8;
    border-color: #c9956a;
}
.stButton > button[kind="primary"] {
    background: #e8c9a0;
    border-color: #c9956a;
    color: #4a2e0e;
}
.stButton > button[kind="primary"]:hover {
    background: #ddb882;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #fff8f0;
    border-color: #e0b88a;
    border-radius: 10px;
    color: #5a3a1a;
}

/* Text input */
.stTextInput > div > div > input {
    background: #fff8f0;
    border-color: #e0b88a;
    border-radius: 10px;
    color: #5a3a1a;
}

/* Sliders */
.stSlider > div { color: #7a5c3a; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #e3cbb0;
    border-right: 1px solid #e8c9a0;
}

/* Info/success boxes */
.stAlert { border-radius: 10px; }

/* Mood badge colors — used via st.markdown */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 99px;
    font-size: 0.82em;
    font-weight: 600;
    margin-right: 4px;
}
.badge-comedy  { background: #FAEEDA; color: #854F0B; }
.badge-horror  { background: #FCEBEB; color: #A32D2D; }
.badge-drama   { background: #E6F1FB; color: #185FA5; }
.badge-action  { background: #EAF3DE; color: #3B6D11; }
.badge-fantasy { background: #EEEDFE; color: #534AB7; }
.badge-romance { background: #FBEAF0; color: #993556; }
.badge-rating  { background: #FAEEDA; color: #854F0B; border-radius: 8px; padding: 2px 10px; font-size: 0.85em; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# favorites bar
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_favorites():
    with open(FAVORITES_FILE, "w") as f:
        json.dump(st.session_state['favorites'], f, indent=2)

def is_favorited(imdb_id):
    return any(m['imdbID'] == imdb_id for m in st.session_state['favorites'])

def add_favorite(movie):
    if not is_favorited(movie['imdbID']):
        entry = {
            "title": movie["Title"],
            "imdbID": movie["imdbID"],
            "poster": movie.get("Poster", "N/A"),
            "year": movie.get("Year", ""),
            "added": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state['favorites'].append(entry)
        save_favorites()
        return True
    return False

def delete_favorite(imdb_id):
    st.session_state['favorites'] = [
        m for m in st.session_state['favorites'] if m['imdbID'] != imdb_id
    ]
    save_favorites()
    st.rerun()

# Movie details
def fetch_details(imdb_id):
    params = {"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "full"}
    return requests.get(BASE_URL, params=params).json()

def show_movie_details(imdb_id, context=""):
    details = fetch_details(imdb_id)
    if details.get("Response") == "True":
        st.markdown("---")
        st.subheader("📋 Movie Details")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            if details.get("Poster") != "N/A":
                st.image(details["Poster"], width=160)
        with col_b:
            rating = details.get("imdbRating", "N/A")
            st.markdown(f'<span class="badge badge-rating">⭐ {rating} / 10</span>', unsafe_allow_html=True)
            st.write(f"**Year:** {details.get('Year')}")
            st.write(f"**Genre:** {details.get('Genre')}")
            st.write(f"**Director:** {details.get('Director')}")
            st.write(f"**Actors:** {details.get('Actors')}")
            st.write(f"**Runtime:** {details.get('Runtime')}")
            trailer_url = f"https://www.youtube.com/results?search_query={details.get('Title','').replace(' ', '+')}+official+trailer"
            st.link_button("▶ Watch Trailer on YouTube", trailer_url)
        st.info(f"**Plot:** {details.get('Plot')}")
        if st.button("Close Details", key=f"close_{context}_{imdb_id}"):
            del st.session_state['selected_id']
            st.rerun()

# Session state
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = load_favorites()
if 'seen_ids' not in st.session_state:
    st.session_state['seen_ids'] = set()
if 'shuffle_history' not in st.session_state:
    st.session_state['shuffle_history'] = []
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = []
if 'last_search_query' not in st.session_state:
    st.session_state['last_search_query'] = ""

# Mood map
mood_map = {
    "I want to laugh 😂":         ("Comedy",  "badge-comedy"),
    "I want a thrill 😱":          ("Horror",  "badge-horror"),
    "I want to think 🤔":          ("Drama",   "badge-drama"),
    "I want some adrenaline 💥":   ("Action",  "badge-action"),
    "I want a fairytale 🦄":       ("Fantasy", "badge-fantasy"),
    "I want to fall in love 💕":   ("Romance", "badge-romance"),
}

st.title("🎬 Movie Mood Generator")

tab1, tab2, tab3 = st.tabs(["✨ Mood Generator", "🔍 Search & Add", "⭐ My Favorites"])

# Tab1
with tab1:
    selected_mood = st.selectbox("What's your mood like today?", list(mood_map.keys()), key="mood_select")
    genre, badge_class = mood_map[selected_mood]

    st.markdown(
        f'<span class="badge {badge_class}">{genre}</span>',
        unsafe_allow_html=True
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        year_range = st.slider("Year range", 1970, 2024, (2000, 2024))
    with col_f2:
        min_rating = st.slider("Min IMDb rating", 0.0, 9.0, 5.0, step=0.5)

    if st.button("Find a movie 🎲", type="primary"):
        params = {
            "apikey": OMDB_API_KEY,
            "s": genre,
            "type": "movie",
            "y": random.randint(year_range[0], year_range[1])
        }
        response = requests.get(BASE_URL, params=params).json()
        if response.get("Response") == "True":
            candidates = [
                m for m in response["Search"]
                if m['imdbID'] not in st.session_state['seen_ids']
            ]
            if not candidates:
                st.session_state['seen_ids'].clear()
                candidates = response["Search"]

            picked = None
            random.shuffle(candidates)
            for candidate in candidates[:5]:
                details = fetch_details(candidate['imdbID'])
                try:
                    if float(details.get("imdbRating", 0)) >= min_rating:
                        picked = candidate
                        picked["imdbRating"] = details.get("imdbRating", "N/A")
                        break
                except (ValueError, TypeError):
                    continue

            if picked:
                st.session_state['seen_ids'].add(picked['imdbID'])
                st.session_state['shuffle_history'].append(picked)
                st.session_state['last_found'] = picked
            else:
                st.warning("No movies matched your filters. Try lowering the rating or widening the year range.")
                st.session_state['last_found'] = None
        else:
            st.error("No movies found for this mood.")
            st.session_state['last_found'] = None

    seen_count = len(st.session_state['seen_ids'])
    if seen_count > 0:
        st.caption(f"🎬 {seen_count} movie(s) shown this session — no repeats!")

    if st.session_state.get('last_found'):
        m = st.session_state['last_found']
        st.subheader(m["Title"])
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if m.get("Poster") and m["Poster"] != "N/A":
                st.image(m["Poster"], width=180)
        with col_info:
            st.write(f"**Year:** {m.get('Year', '')}")
            if m.get("imdbRating"):
                st.markdown(f'<span class="badge badge-rating">⭐ {m["imdbRating"]} / 10</span>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button("View Details", key="det_tab1"):
                st.session_state['selected_id'] = m['imdbID']
            if is_favorited(m['imdbID']):
                col2.success("In favorites ✓")
            elif col2.button("Add to Favorites ❤️", key="add_tab1"):
                add_favorite(m)
                st.success("Added!")
                st.rerun()

        if st.session_state.get('selected_id') == m['imdbID']:
            show_movie_details(m['imdbID'], context="tab1")

    if len(st.session_state['shuffle_history']) > 1:
        with st.expander(f"📜 Session history ({len(st.session_state['shuffle_history'])} movies)"):
            for h in reversed(st.session_state['shuffle_history'][:-1]):
                hc1, hc2 = st.columns([3, 1])
                hc1.write(f"**{h['Title']}** ({h.get('Year', '')})")
                if hc2.button("Re-pick", key=f"repick_{h['imdbID']}"):
                    st.session_state['last_found'] = h
                    st.rerun()

# Tab2
with tab2:
    search_query = st.text_input("Enter movie name:", value=st.session_state['last_search_query'])

    if st.button("Search", type="primary"):
        clean_query = search_query.strip()
        if len(clean_query) < 2:
            st.warning("Please enter at least 2 characters.")
        else:
            res = requests.get(BASE_URL, params={
                "apikey": OMDB_API_KEY,
                "s": clean_query,
                "type": "movie"
            }).json()
            if res.get("Response") == "True":
                st.session_state['search_results'] = res["Search"]
                st.session_state['last_search_query'] = clean_query
            else:
                st.session_state['search_results'] = []
                st.error("Nothing found.")

    for movie in st.session_state.get('search_results', []):
        with st.container():
            c1, c2 = st.columns([1, 4])
            if movie.get("Poster") != "N/A":
                c1.image(movie["Poster"], width=80)
            c2.markdown(f"**{movie['Title']}** ({movie['Year']})")

            b1, b2 = st.columns([1, 2])
            if b1.button("Details", key=f"v_{movie['imdbID']}"):
                if st.session_state.get('selected_id') == movie['imdbID']:
                    del st.session_state['selected_id']
                else:
                    st.session_state['selected_id'] = movie['imdbID']
                st.rerun()

            if is_favorited(movie['imdbID']):
                b2.success("In favorites ✓")
            elif b2.button("Add ❤️", key=f"a_{movie['imdbID']}"):
                add_favorite(movie)
                st.rerun()

            if st.session_state.get('selected_id') == movie['imdbID']:
                show_movie_details(movie['imdbID'], context="tab2")
            st.divider()

# Tab3 
with tab3:
    favs = st.session_state['favorites']
    if not favs:
        st.info("No favorites yet. Find movies you love and add them!")
    else:
        st.write(f"**{len(favs)} saved movie(s)**")
        for fav in list(favs):
            with st.container():
                fc1, fc2, fc3 = st.columns([1, 4, 1])
                if fav.get("poster") and fav["poster"] != "N/A":
                    fc1.image(fav["poster"], width=70)
                with fc2:
                    st.markdown(f"**{fav['title']}** ({fav.get('year', '')})")
                    st.caption(f"Added {fav.get('added', '')}")
                    trailer_url = f"https://www.youtube.com/results?search_query={fav['title'].replace(' ', '+')}+official+trailer"
                    st.link_button("▶ Trailer", trailer_url)
                if fc3.button("🗑️", key=f"del_{fav['imdbID']}"):
                    delete_favorite(fav['imdbID'])
                st.divider()

# Siderbar
st.sidebar.header("⭐ Quick Favorites")
favs = st.session_state['favorites']
if favs:
    for fav in favs[-5:]:
        st.sidebar.markdown(f"• {fav['title']} ({fav.get('year', '')})")
    if len(favs) > 5:
        st.sidebar.caption(f"...and {len(favs) - 5} more in the Favorites tab")
else:
    st.sidebar.info("No favorites yet.")

st.sidebar.markdown("---")
st.sidebar.caption(f"🎬 {len(st.session_state['seen_ids'])} movies seen this session")