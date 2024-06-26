#!/usr/bin/env python
# coding: utf-8

# In[87]:


import requests
import base64
import pandas as pd
import streamlit as st

# Adjust display options
pd.set_option('display.max_rows', None)   # Show all rows
pd.set_option('display.max_columns', None)   # Show all columns


# In[88]:


CLIENT_ID = 'fe625cd1e17f45cca39c0fbb4b9b4313'
CLIENT_SECRET = '5d59a2b5904441c39e26384d1399be1c'

# Base64 encode the client ID and client secret
client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
client_credentials_base64 = base64.b64encode(client_credentials.encode())

# Request the access token
token_url = 'https://accounts.spotify.com/api/token'
headers = {
    'Authorization': f'Basic {client_credentials_base64.decode()}'
}
data = {
    'grant_type': 'client_credentials'
}
response = requests.post(token_url, data=data, headers=headers)

if response.status_code == 200:
    access_token = response.json()['access_token']
    print("Access token obtained successfully.")
else:
    print("Error obtaining access token.")
    exit()


# In[89]:
#import pandas as pd
#import spotipy
#from spotipy.oauth2 import SpotifyOAuth
from utilities import get_trending_playlist_data





# In[90]:
#playlist_id = '3rNqxghsSqsloXkPly9FIU'
playlist_id = '37i9dQZF1DXcBWIGoYBM5M' #Today's Top Hits

# Call the function to get the music data from the playlist and store it in a DataFrame
music_df = get_trending_playlist_data(playlist_id, access_token)
music_df.head()


# In[91]:


#check for null and duplicates
print(music_df.isna().sum())
print( "No. of duplicates:" + str(music_df.duplicated().sum()))


# In[92]:


#Building the ML Model
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

data = music_df


# In[93]:

@st.cache_data
# Function to calculate weighted popularity scores based on release date
def calculate_weighted_popularity(release_date):
    # Convert the release date to datetime object
    release_date = datetime.strptime(release_date, '%Y-%m-%d')

    # Calculate the time span between release date and today's date
    time_span = datetime.now() - release_date

    # Calculate the weighted popularity score based on time span (e.g., more recent releases have higher weight)
    weight = 1 / (time_span.days + 1)
    return weight


# In[94]:


# Normalize the music features using Min-Max scaling
scaler = MinMaxScaler()
music_features = music_df[['Danceability', 'Energy', 'Key', 
                           'Loudness', 'Mode', 'Speechiness', 'Acousticness',
                           'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values
music_features_scaled = scaler.fit_transform(music_features)


# In[95]:

@st.cache_data
# a function to get content-based recommendations based on music features
def content_based_recommendations(input_song_name, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    # Get the index of the input song in the music DataFrame
    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]

    # Calculate the similarity scores based on music features (cosine similarity)
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)

    # Get the indices of the most similar songs by descending order of similarity scores
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]

    # Get the names of the most similar songs based on content-based filtering
    content_based_recommendations = music_df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]

    return content_based_recommendations

# In[97]:

@st.cache_data
# a function to get hybrid recommendations based on weighted popularity
def hybrid_rec(input_song_name, num_recommendations=5, alpha=0.5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    # Get content-based recommendations
    content_based_rec = content_based_recommendations(input_song_name, num_recommendations)

    # Get the popularity score of the input song
    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]

    # Calculate the weighted popularity score
    weighted_popularity_score = popularity_score * calculate_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])

    # Combine content-based and popularity-based recommendations based on weighted popularity
    hybrid_recommendations = content_based_rec
    #hybrid_recommendations = hybrid_recommendations.append({
       # 'Track Name': input_song_name,
       # 'Artists': music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0],
       # 'Album Name': music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0],
      #  'Release Date': music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0],
       # 'Popularity': weighted_popularity_score
   # }, ignore_index=True)
    new_row = pd.DataFrame([{
    'Track Name': input_song_name,
    'Artists': music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0],
    'Album Name': music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0],
    'Release Date': music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0],
    'Popularity': weighted_popularity_score
     }])

    hybrid_recommendations = pd.concat([hybrid_recommendations, new_row], ignore_index=True)


    # Sort the hybrid recommendations based on weighted popularity score
    hybrid_recommendations = hybrid_recommendations.sort_values(by='Popularity', ascending=False)

    # Remove the input song from the recommendations
    hybrid_recommendations = hybrid_recommendations[hybrid_recommendations['Track Name'] != input_song_name]


    return hybrid_recommendations

# In[98]:


import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")


# In[101]:


# song_name = '小胡同'
song_name = 'MELTDOWN (feat. Drake)'
recommendations = hybrid_rec(song_name, num_recommendations=5)
print(f"Hybrid recommended songs for '{song_name}':")
recommendations


# %%

import streamlit as st
import pandas as pd

st.title('Spotify Music Recommendations')

# Replace hardcoded playlist_id and song_name with user inputs
#playlist_id = st.text_input("Enter Spotify Playlist ID:", '3rNqxghsSqsloXkPly9FIU')
playlist_id = st.text_input("Enter Spotify Playlist ID:")
song_name = st.text_input("Enter a song name for recommendations:")


if playlist_id and song_name:
    # You might need to ensure that access_token is fetched or defined before this line
    music_df = get_trending_playlist_data(playlist_id, access_token)
    st.dataframe(music_df.head())  # Display the first few rows of the dataframe

    if st.button('Get Recommendations'):
        recommendations = hybrid_rec(song_name, num_recommendations=5)
        st.write(f"Hybrid recommended songs for '{song_name}':")
        st.dataframe(recommendations)



'''
import streamlit as st
import pandas as pd

# Import Streamlit at the beginning
st.title('Spotify Music Recommendations')

# Replace hardcoded playlist_id and song_name with user inputs
playlist_id = st.text_input("Enter Spotify Playlist ID:", '3rNqxghsSqsloXkPly9FIU')
song_name = st.text_input("Enter a song name for recommendations:")

# Display the DataFrame
if playlist_id and song_name:
    music_df = get_trending_playlist_data(playlist_id, access_token)
    st.dataframe(music_df.head())  # Display the first few rows of the dataframe

    if st.button('Get Recommendations'):
        recommendations = hybrid_rec(song_name, num_recommendations=5)
        st.write(f"Hybrid recommended songs for '{song_name}':")
        st.dataframe(recommendations)
'''
