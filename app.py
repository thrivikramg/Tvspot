import streamlit as st
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# -------------------- 🔐 Spotify App Secrets --------------------
try:
    CLIENT_ID = st.secrets["SPOTIPY_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["SPOTIPY_CLIENT_SECRET"]
    REDIRECT_URI = st.secrets["SPOTIPY_REDIRECT_URI"]
except KeyError as e:
    st.error(f"Missing secret: {e}. Please set it in Streamlit Cloud → Settings → Secrets.")
    st.stop()

SCOPE = "playlist-modify-public playlist-modify-private user-read-private"

# -------------------- 🎨 Background Styling --------------------
BACKGROUND_IMAGE = "https://images.unsplash.com/photo-1647866872319-683f5c4c56e6?fm=jpg&q=60&w=3000"

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BACKGROUND_IMAGE}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: white !important;
        font-weight: bold;
    }}
    header, footer, .viewerBadge_container__1QSob {{
        display: none !important;
    }}
    .stTextInput > div > label, .stTextInput > div > input {{
        color: white !important;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-weight: bold;
    }}
    .stButton > button {{
        background: linear-gradient(145deg, #FFD700, #FFA500);
        color: black;
        font-weight: bold;
        border-radius: 12px;
        box-shadow: 0px 0px 10px #FFD700;
    }}
    .stButton > button:hover {{
        background: linear-gradient(145deg, #FFC300, #FFB347);
    }}
    h1 {{
        text-align: center;
        color: white;
        font-weight: bold;
        font-size: 2.5rem;
        text-shadow: 0 0 15px #FFD700;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>✨ Spotify Playlist Maker</h1>", unsafe_allow_html=True)

# -------------------- ⚙️ Spotify Auth Manager --------------------
@st.cache_resource(show_spinner=False)
def get_auth_manager():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".cache",
        show_dialog=True
    )

auth_manager = get_auth_manager()

# -------------------- 📦 Session State Init --------------------
for key in ["token_info", "sp", "playlist_id", "code"]:
    if key not in st.session_state:
        st.session_state[key] = None

# -------------------- 🔁 OAuth Callback Handler --------------------
query_params = st.query_params

if not st.session_state.token_info and "code" in query_params:
    code = query_params["code"]
    try:
        token_info = auth_manager.get_access_token(code, as_dict=True)
        if token_info:
            st.session_state.token_info = token_info
            st.session_state.sp = Spotify(auth=token_info['access_token'])
            st.session_state.code = code
            st.query_params.clear()  # Clear query parameters from URL
            st.rerun()
    except Exception as e:
        st.error(f"OAuth Error: {e}")
        st.stop()

# -------------------- 🟢 Authenticated State --------------------
if st.session_state.token_info:
    sp = st.session_state.sp or Spotify(auth=st.session_state.token_info["access_token"])
    st.session_state.sp = sp
    try:
        user = sp.current_user()
        st.success(f"✅ Logged in as {user['display_name']} ({user['id']})", icon="✅")

        # 🎧 Playlist Creation
        playlist_name = st.text_input("Enter Playlist Name")
        if st.button("🎵 Create Playlist"):
            if not playlist_name.strip():
                st.error("Please enter a valid playlist name.")
            else:
                new_playlist = sp.user_playlist_create(user["id"], playlist_name)
                st.session_state.playlist_id = new_playlist["id"]
                st.success(f"Playlist '{playlist_name}' created!", icon="🎉")

        # ➕ Add Songs
        if st.session_state.playlist_id:
            song_name = st.text_input("Enter Song Name")
            if st.button("➕ Add Song"):
                if not song_name.strip():
                    st.error("Please enter a song name.")
                else:
                    results = sp.search(q=song_name, type="track", limit=1)
                    tracks = results["tracks"]["items"]
                    if tracks:
                        track = tracks[0]
                        sp.playlist_add_items(st.session_state.playlist_id, [track["uri"]])
                        st.success(f"✅ Added '{track['name']}' by {track['artists'][0]['name']}' to playlist!")
                    else:
                        st.warning("⚠️ Song not found.")

        # 🚪 Logout
        if st.button("🚪 Logout"):
            for key in ["sp", "token_info", "playlist_id", "code"]:
                st.session_state[key] = None
            st.query_params.clear()
            st.rerun()

    except SpotifyException as e:
        st.error("Spotify API Error: " + str(e))
        for key in ["sp", "token_info", "playlist_id", "code"]:
            st.session_state[key] = None
        st.query_params.clear()
        st.rerun()

# -------------------- 🟡 Not Logged In --------------------
else:
    login_url = auth_manager.get_authorize_url()
    st.markdown(f"### [🔐 Click here to login with Spotify]({login_url})")
