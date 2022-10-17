import pickle
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image


def score(user_id, item_id, Nmax=20):
    assert Nmax > 1

    items_rated_by_user = ratings_df[ratings_df['user_id'] == user_id].dropna()

    if items_rated_by_user.empty:
        popular = popular_items.index[0]
        return popular

    item_sim_ratings = pd.DataFrame(item_sim.loc[item_id]).reset_index()
    item_sim_ratings.columns = ['movie_id', 'sim']

    df_temp = items_rated_by_user.merge(item_sim_ratings).sort_values('sim', ascending=False).iloc[0:Nmax]
    # retval= np.average(df_temp['ratings'], weights=df_temp['sim'])

    # this compensates for pathelogical cases where negative correltions dominate
    ret_num = (df_temp['rating'] * df_temp['sim']).sum()
    ret_den = df_temp['sim'].abs().sum()
    retval = ret_num / (1.0 * ret_den)

    return np.clip(retval, min_rating, max_rating)


def items_to_search(user_id, k=50):
    items_rated_by_user = ratings_df[ratings_df['user_id'] == user_id].dropna()['movie_id']
    items_not_rated_by_user = set(ratings_df['movie_id']) - set(items_rated_by_user)
    data = [item_frequency[i] for i in items_not_rated_by_user]
    topk = pd.Series(data=data, index=items_not_rated_by_user).nlargest(k).index

    # return list(items_not_rated_by_user)
    return list(topk)


def calculate_all_item_suggestions(user_id, max_suggestions=30):
    item_search_list = items_to_search(user_id, k=max_suggestions)
    scores = {}

    for item_id in item_search_list:
        s = score(user_id, item_id, 30)  # Nmax=30
        scores[item_id] = s

    return pd.Series(scores)


def reccomend(user_id):
    retval = calculate_all_item_suggestions(user_id).nlargest(5)
    recos = items[items['movie_id'].isin(retval.index)][['title']]
    recos_id = items[items['movie_id'].isin(retval.index)][['movie_id']]

    recommended_movies = []
    recommended_movies_posters = []

    for j in recos_id.movie_id:
        movies_id = j
        recommended_movies_posters.append(fetch_poster(movies_id))

    for i in recos.title:
        recommended_movies.append(i)

    return recommended_movies, recommended_movies_posters


def fetch_poster(movie_id):
    response = requests.get(
        "https://api.themoviedb.org/3/movie/{}?api_key=ce3e3e03053ce84779d05fc694470a6d&language=en-US".format(
            movie_id))
    data = response.json()
    return "https://image.tmdb.org/t/p/w500/" + data["poster_path"]


ratings_df = pickle.load(open("dataset.pkl", "rb"))
item_sim = pickle.load(open("item_sim.pkl", "rb"))
min_rating = pickle.load(open("min_rating.pkl", "rb"))
max_rating = pickle.load(open("max_rating.pkl", "rb"))
popular_items = pickle.load(open("popular_items.pkl", "rb"))
item_frequency = pickle.load(open("item_frequency.pkl", "rb"))
items = pickle.load(open("items.pkl", "rb"))

st.title("WizardTales Movie Recommender System Demo Page")

image = Image.open("a.jpg")
st.image(image, width=200)

selected_user_name = st.selectbox(
    "Please choose a customer id.",
    (ratings_df["user_id"].values))

if st.button("Recommend"):
    names, posters = reccomend(selected_user_name)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.text(names[0])
        st.image(posters[0])

    with col2:
        st.text(names[1])
        st.image(posters[1])

    with col3:
        st.text(names[2])
        st.image(posters[2])

    with col4:
        st.text(names[3])
        st.image(posters[3])

    with col5:
        st.text(names[4])
        st.image(posters[4])
