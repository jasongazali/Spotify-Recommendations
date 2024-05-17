#!/usr/bin/env python
# coding: utf-8

import requests
import base64
import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from utilities import get_trending_playlist_data
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Adjust display options
#pd.set_option('display.max_rows', None)  # Show all rows
#pd.set_option('display.max_columns', None)  # Show all columns

CLIENT_ID = 'fe625cd1e17f45cca39c0fbb4b9b4313'
CLIENT_SECRET = '5d59a2b5904441c39e26384d1399be1c'

def fetch_access_token():
    client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_credentials_base64 = base64.b64encode(client_credentials.encode())
    token_url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': f'Basic {client_credentials_base64.decode()}'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Error obtaining access token.")

from utilities import cached_get_trending_playlist_data

def calculate_weighted_popularity(release_date):
    release_date = datetime.strptime(release_date, '%Y-%m-%d')
    time_span = datetime.now() - release_date
    return 1 / (time_span.days + 1)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri="https://localhost:8407/callback",
    #redirect_uri= "statso.io",  # Make sure this matches with your app's redirect URI
    scope="playlist-modify-private playlist-modify-public",
    cache_path=".cache"
))

def create_playlist(name, public=True):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, name, public=public)
    return playlist['id']

def add_tracks_to_playlist(playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)


@st.cache_data(ttl=3600)
def get_content_based_recommendations(music_df, music_features_scaled, input_song_name, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        st.error(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return pd.DataFrame()

    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]
    return music_df.iloc[similar_song_indices]

@st.cache_data(ttl=3600)
def get_hybrid_recommendations(music_df, music_features_scaled, input_song_name, num_recommendations=5, alpha=0.5):
    content_based_rec = get_content_based_recommendations(music_df, music_features_scaled, input_song_name, num_recommendations)
    if content_based_rec.empty:
        return pd.DataFrame()

    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]
    weighted_popularity_score = popularity_score * calculate_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])

    new_row = pd.DataFrame([{
        'Track Name': input_song_name,
        'Artists': music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0],
        'Album Name': music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0],
        'Release Date': music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0],
        'Popularity': weighted_popularity_score
    }])

    hybrid_recommendations = pd.concat([content_based_rec, new_row], ignore_index=True)
    hybrid_recommendations = hybrid_recommendations.sort_values(by='Popularity', ascending=False)
    return hybrid_recommendations[hybrid_recommendations['Track Name'] != input_song_name]


def set_background_image():
    background_image = 'https://miro.medium.com/v2/resize:fit:1400/format:webp/1*xlsvfw090Y_ONaPnXJmsTA.png'  # Replace with your image URL
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{background_image}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    track_uris = []
    set_background_image()
    st.title('Spotify Music Recommendations')

    access_token = fetch_access_token()

    playlist_id = st.text_input("Enter Spotify Playlist ID:")
    song_name = st.text_input("Enter a song name for recommendations:")

    # Check if we need to fetch new data or use cached data
    if playlist_id:
        if 'music_df' not in st.session_state or st.session_state.playlist_id != playlist_id:
            # Cache the playlist ID and fetch new data
            st.session_state.playlist_id = playlist_id
            music_df = cached_get_trending_playlist_data(playlist_id, access_token)
            st.session_state.music_df = music_df
            # Display data frame head
            st.dataframe(music_df.head())

            # Perform scaling
            scaler = MinMaxScaler()
            music_features = music_df[['Danceability', 'Energy', 'Key', 'Loudness', 'Mode', 'Speechiness', 
                                       'Acousticness', 'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values
            music_features_scaled = scaler.fit_transform(music_features)
            st.session_state.music_features_scaled = music_features_scaled
        else:
            # Use cached data
            music_df = st.session_state.music_df
            music_features_scaled = st.session_state.music_features_scaled
            st.dataframe(music_df.head())

        if song_name and st.button('Get Recommendations'):
            # Generate and display recommendations
            recommendations = get_hybrid_recommendations(music_df, music_features_scaled, song_name)
            st.write(f"Recommended songs for '{song_name}':")
            st.dataframe(recommendations)

            #track_uris = []
            for track_id in recommendations['Track ID'].tolist():
                track_uris.append('spotify:track:' + track_id)
            #   recommendations['Track ID'].tolist()

        if st.button('Create Spotify Playlist'):
            #st.write('Button was clicked!')
            playlist_name = f"Recommendations for {song_name}"
            playlist_id_create = create_playlist(playlist_name, public=False)  # Create a private playlist
            add_tracks_to_playlist(playlist_id_create, track_uris)
            st.success('Playlist created successfully!')
            st.markdown(f"Playlist created successfully! [View Playlist](https://open.spotify.com/playlist/{playlist_id_create})")


    else:
        st.warning("Please enter a Spotify Playlist ID.")

if __name__ == "__main__":
    main()

