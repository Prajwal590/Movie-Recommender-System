import streamlit as st
import pickle
import pandas as pd
import requests

# API keys
API_KEY_TMDB = '209d8b06e6a1f07855f0483a2ad0bf79'
API_KEY_OMDB = '77a3e813'

# Background image URL
background_image_url = "https://styles.redditmedia.com/t5_29xk0x/styles/bannerBackgroundImage_xdhyb1paw0sb1.jpg?format=pjpg&s=02d92e850f9dcbe53157d4b900fcecaf42e69cd9"  # Replace with your image URL

# Custom CSS to set the background image
page_bg_css = f"""
<style>
    .stApp {{
        background-image: url({background_image_url});
        background-size: cover;
        background-position: center;
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p {{
        color: white;
    }}
    .stTextInput {{
        color: white;
    }}
</style>
"""

st.markdown(page_bg_css, unsafe_allow_html=True)

# Function to fetch movie details from TMDB API
def fetch_movie_details_tmdb(movie_id):
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY_TMDB}&language=en-US')
    data = response.json()
    poster_path = data.get('poster_path')
    movie_url = f"https://www.themoviedb.org/movie/{movie_id}"
    rating = data.get('vote_average', 0) / 2  # Convert 10-point scale to 5-point scale
    
    if poster_path:
        poster_url = "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        poster_url = "https://via.placeholder.com/500x750?text=No+Image"
    
    return poster_url, movie_url, rating

# Function to fetch movie details from OMDb API
def fetch_movie_details_omdb(imdb_id):
    response = requests.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey={API_KEY_OMDB}')
    data = response.json()
    if data['Response'] == 'True':
        poster_url = data.get('Poster', 'https://via.placeholder.com/500x750?text=No+Image')
        movie_url = f"https://www.imdb.com/title/{imdb_id}/"
        rating = float(data.get('imdbRating', 0)) / 2  # Convert IMDb rating to 5-point scale
    else:
        poster_url = "https://via.placeholder.com/500x750?text=No+Image"
        movie_url = ""
        rating = 0.0
    
    return poster_url, movie_url, rating

# Function to recommend movies based on similarity (using TMDB data)
def recommend(movie, movies, similarity):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]

    recommended_movies = []
    recommended_movies_posters = []
    recommended_movies_urls = []
    recommended_movies_ratings = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]]['movie_id']
        poster_url, movie_url, rating = fetch_movie_details_tmdb(movie_id)
        recommended_movies.append(movies.iloc[i[0]]['title'])
        recommended_movies_posters.append(poster_url)
        recommended_movies_urls.append(movie_url)
        recommended_movies_ratings.append(rating)
    return recommended_movies, recommended_movies_posters, recommended_movies_urls, recommended_movies_ratings

# Function to fetch actor's movies from TMDB API
def fetch_actor_movies(actor_name):
    try:
        response = requests.get(f'https://api.themoviedb.org/3/search/person?api_key={API_KEY_TMDB}&language=en-US&query={actor_name}')
        data = response.json()
        
        if 'results' in data and data['results']:
            actor_id = data['results'][0]['id']
            response = requests.get(f'https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={API_KEY_TMDB}&language=en-US')
            movies = response.json().get('cast', [])
            
            actor_movies = []
            actor_movies_posters = []
            actor_movies_urls = []
            actor_movies_ratings = []
            
            for movie in movies:
                title = movie.get('title', 'Unknown Title')
                poster_path = movie.get('poster_path')
                movie_id = movie.get('id', '')
                
                if poster_path:
                    poster_url = "https://image.tmdb.org/t/p/w500/" + poster_path
                else:
                    poster_url = "https://via.placeholder.com/500x750?text=No+Image"
                
                actor_movies.append(title)
                actor_movies_posters.append(poster_url)
                actor_movies_urls.append(f"https://www.themoviedb.org/movie/{movie_id}")
                actor_movies_ratings.append(movie.get('vote_average', 0) / 2)
            
            return actor_movies, actor_movies_posters, actor_movies_urls, actor_movies_ratings
        
        else:
            return [], [], [], []
    
    except Exception as e:
        st.error(f"Error fetching actor movies: {str(e)}")
        return [], [], [], []

# Function to fetch movies by genre from TMDB API
def fetch_movies_by_genre(genre_id):
    response = requests.get(f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY_TMDB}&with_genres={genre_id}')
    data = response.json()
    movies = data.get('results', [])
    genre_movies = []
    genre_movies_posters = []
    genre_movies_urls = []
    genre_movies_ratings = []
    for movie in movies:
        genre_movies.append(movie['title'])
        poster_url = "https://image.tmdb.org/t/p/w500/" + movie.get('poster_path', '')
        genre_movies_posters.append(poster_url)
        genre_movies_urls.append(f"https://www.themoviedb.org/movie/{movie['id']}")
        genre_movies_ratings.append(movie.get('vote_average', 0) / 2)
    return genre_movies, genre_movies_posters, genre_movies_urls, genre_movies_ratings

# Load movies and similarity matrices (replace with your actual file paths)
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("Error: The data files are missing. Please ensure they are available.")

# Genres dictionary
genres = {
    'Action': 28,
    'Adventure': 12,
    'Animation': 16,
    'Comedy': 35,
    'Crime': 80,
    'Documentary': 99,
    'Drama': 18,
    'Family': 10751,
    'Fantasy': 14,
    'History': 36,
    'Horror': 27,
    'Music': 10402,
    'Mystery': 9648,
    'Romance': 10749,
    'Science Fiction': 878,
    'TV Movie': 10770,
    'Thriller': 53,
    'War': 10752,
    'Western': 37
}

# Streamlit UI
st.title('Movie Recommender System')

# Recommendation based on selected movie
selected_movie_name = st.selectbox(
    "Select a movie:",
    movies['title'].values if 'movies' in locals() else []
)

if st.button("Recommend"):
    if 'movies' in locals() and 'similarity' in locals():
        names, posters, urls, ratings = recommend(selected_movie_name, movies, similarity)

        cols = st.columns(5)

        for i in range(min(10, len(names))):
            with cols[i % 5]:
                st.text(names[i])
                st.image(posters[i])
                st.markdown(f"[Watch Now]({urls[i]})", unsafe_allow_html=True)
                st.text(f"Rating: {ratings[i]:.1f} / 5")
    else:
        st.error("Error: Data files not loaded.")

# Actor search
st.title('Actor Search')

actor_name = st.text_input("Enter actor's name:")

if st.button("Search"):
    actor_movies, actor_movies_posters, actor_movies_urls, actor_movies_ratings = fetch_actor_movies(actor_name)

    if actor_movies:
        st.write(f"Movies featuring {actor_name}:")
        cols = st.columns(5)
        for i in range(len(actor_movies)):
            with cols[i % 5]:
                st.text(actor_movies[i])
                st.image(actor_movies_posters[i])
                st.markdown(f"[Watch Now]({actor_movies_urls[i]})", unsafe_allow_html=True)
                st.text(f"Rating: {actor_movies_ratings[i]:.1f} / 5")
    else:
        st.write(f"No movies found for actor {actor_name}.")

# Genre search
st.title('Genre Search')

selected_genre = st.selectbox(
    "Select a genre:",
    list(genres.keys())
)

if st.button("Search by Genre"):
    genre_id = genres[selected_genre]
    genre_movies, genre_movies_posters, genre_movies_urls, genre_movies_ratings = fetch_movies_by_genre(genre_id)

    if genre_movies:
        st.write(f"Movies in {selected_genre} genre:")
        cols = st.columns(5)
        for i in range(len(genre_movies)):
            with cols[i % 5]:
                st.text(genre_movies[i])
                st.image(genre_movies_posters[i])
                st.markdown(f"[Watch Now]({genre_movies_urls[i]})", unsafe_allow_html=True)
                st.text(f"Rating: {genre_movies_ratings[i]:.1f} / 5")