import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Set page config
st.set_page_config(page_title="TVSpot Spotify Auth", layout="centered")

# Load secrets
CLIENT_ID = st.secrets["SPOTIPY_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SPOTIPY_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["SPOTIPY_REDIRECT_URI"]

# Define scope
SCOPE = "user-read-playback-state user-read-currently-playing user-library-read"

# Setup Spotify OAuth
auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    show_dialog=True
)

# Try to retrieve token from session or redirect back
if "token_info" not in st.session_state:
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        try:
            code = query_params["code"][0]
            token_info = auth_manager.get_access_token(code, as_dict=True)
            st.session_state.token_info = token_info
        except spotipy.SpotifyOauthError as e:
            st.error(f"Spotify OAuth failed: {e}")
            st.stop()
    else:
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f"[Click here to log in with Spotify]({auth_url})")
        st.stop()

# Initialize Spotify object with token
sp = spotipy.Spotify(auth=st.session_state.token_info["access_token"])

# Show user playback info
st.header("🎵 Currently Playing on Spotify")
playback = sp.current_playback()

if playback and playback["is_playing"]:
    track = playback["item"]
    st.subheader(f"{track['name']} — {', '.join([a['name'] for a in track['artists']])}")
    st.image(track['album']['images'][0]['url'], width=300)
else:
    st.write("Nothing is playing right now.")
