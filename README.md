---

# Music Recommendations with Spotify API

## Overview
This project focuses on building a music recommendation system using the Spotify API. It fetches data from Spotify playlists and utilizes various features of the tracks to recommend similar music based on content and popularity.

## Key Features
- **Spotify API Integration**: Authenticates with the Spotify API to access music data.
- **Playlist Data Fetching**: Retrieves data from specified Spotify playlists.
- **Data Analysis**: Processes and analyzes track data using `pandas` and `spotipy`.
- **Recommendation System**:
  - **Content-Based Recommendations**: Generates recommendations based on the similarity of music features like danceability, energy, etc.
  - **Hybrid Recommendations**: Combines content-based recommendations with a weighted popularity score, factoring in the release date of tracks.

## Requirements
- Python 3
- Libraries: `requests`, `base64`, `pandas`, `spotipy`

## Usage
1. **API Authentication**: Provide your Spotify Client ID and Secret to authenticate and obtain an access token.
2. **Get Playlist Data**: Use the `get_trending_playlist_data` function with a playlist ID to fetch track data.
3. **Data Analysis**: Explore and analyze the track data with pandas DataFrame.
4. **Generate Recommendations**:
   - Use `content_based_recommendations` for content-based recommendations.
   - Use `hybrid_recommendations` for a mix of content-based and popularity-based recommendations.

## Getting Started
Replace the `CLIENT_ID` and `CLIENT_SECRET` in the notebook with your Spotify API credentials. Choose a playlist ID of your choice and use the provided functions to get music recommendations.

## Note
Ensure you have all the required libraries installed. You can install them using pip:

```bash
pip install pandas spotipy requests
```

---
