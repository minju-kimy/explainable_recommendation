import random

from flask import Blueprint, render_template, request, url_for, session
from app import db
from werkzeug.utils import redirect

from datetime import datetime
from app.models import Movie, User, Favorite_movie, Recommended_movie

#processing
from os.path import join, dirname, realpath
import pandas as pd
from surprise import SVD, Reader, Dataset

import random

import networkx as nx


bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/test')
def test():
    if request.method == 'POST':
        name = request.form['name']
        favorite = request.form['favorite']
        dislike = request.form['dislike']


        info_data = User(name = name, favorite_genre = favorite, unfavorite_genre = dislike, create_date = datetime.now())
        db.session.add(info_data)
        db.session.commit()

    return render_template('movie_page.html')

    # return redirect(url_for('movie_page'))

    # return render_template('test.html', name=name, favorite=favorite, dislike=dislike)


@bp.route('/home')
def home():
    return render_template('home.html')

@bp.route('/movie_page', methods=['GET', 'POST'])
def movie_page():

    if request.method == 'POST':
        name = request.form['name']
        favorite = request.form['favorite']
        dislike = request.form['dislike']

        #db 저장
        info_data = User(name = name, favorite_genre = favorite, unfavorite_genre = dislike, create_date = datetime.now())
        db.session.add(info_data)
        db.session.commit()

        #db에서 user id값 > info_data.id
        session.clear()
        session['user_id'] = info_data.id

    movies = Movie.query.all()
    return render_template('movie_page.html', movies=movies)

@bp.route('/recommended_movie', methods=['GET', 'POST'])
def processing():

    user_id = session['user_id']

    # read data and save data
    read_favorite_movie(user_id)

    # prediction and save recommended movie
    prediction(user_id)

    # recommend 영화 출력
    recommended_movies = Recommended_movie.query.filter_by(user_id = user_id).all()
    return render_template('recommended_movie.html', recommended_movies = recommended_movies)


def read_favorite_movie(user_id):
    if request.method == 'POST':
        data = (request.form).getlist('favorite_movie')

        for favorite_movie in data:
            user_id = user_id
            movie_id = favorite_movie
            movie_name = Movie.query.filter_by(id = movie_id).first().name
            create_date = datetime.now()

            #db 저장
            movie_data = Favorite_movie(user_id = user_id, movie_id = movie_id, movie_name = movie_name, create_date = create_date)
            db.session.add(movie_data)
            db.session.commit()

    return

def prediction(user_id):
    # read rating csv
    rating = pd.read_csv(join(realpath('top200_movie_rating.csv')))
    top200_movie = pd.read_csv(join(realpath('top200_movie.csv')))

    col = ['userId', 'title_only', 'rating']
    rating = rating[col]

    tmp = Favorite_movie.query.filter_by(user_id = user_id).all()
    movie_names = []
    for movie in tmp:
        movie_names.append(movie.movie_name)

    #add user data
    for movie_name in movie_names:
        rating = rating.append({'userId':str(user_id), 'title_only':movie_name, 'rating':5}, ignore_index=True)

    #surpise dataset
    reader = Reader(rating_scale=(0.5, 5))
    data = Dataset.load_from_df(rating, reader)
    trainset = data.build_full_trainset()

    #train
    algo = SVD()
    algo.fit(trainset)

    # recommended movie extraction
    seen_movies = movie_names
    total_movies =top200_movie['title_only'].tolist()
    unseen_movies = [movie for movie in total_movies if movie not in seen_movies]

    predictions = []
    for movieName in unseen_movies:
        predictions.append(algo.predict(str(user_id), str(movieName)))

    predictions.sort(key=sortkey_est, reverse=True)
    top_predictions = predictions[:5]

    for pred in top_predictions:
        movie_name = pred.iid
        tmp = Movie.query.filter_by(name=movie_name).first()
        movie_predicted_rating = pred.est
        movie_id = tmp.id
        create_date = datetime.now()
        link_id = tmp.link_id
        genres = tmp.genres

        # db 저장
        recommends = Recommended_movie(user_id=user_id, movie_id=movie_id, movie_name=movie_name, predicted_rating = movie_predicted_rating, link_id = link_id, genres = genres, create_date=create_date)
        db.session.add(recommends)
        db.session.commit()

    return


def sortkey_est(pred):
    return pred.est


@bp.route('/result', methods=['GET', 'POST'])
def result():

    user_id = session['user_id']

    # 그래프 생성
    graph = create_graph(user_id)

    # 추천영화 정보 읽어오기
    tmp = Recommended_movie.query.filter_by(user_id=user_id).all()

    # 비선호장르제외
    dislike_genre = User.query.filter_by(id=user_id).first().unfavorite_genre

    result = []
    for recommended_movie in tmp:
        if dislike_genre in recommended_movie.genres:
            continue
        removie = [p for p in nx.all_shortest_paths(graph, source=str(user_id), target=recommended_movie.movie_name)]
        if len(removie) > 3:
            removie = random.sample(removie, 3)
        result = result + removie



    return render_template('result.html', result = result)

def create_graph(user_id):
    # movielens data
    top200_movie_rating = pd.read_csv(join(realpath('top200_movie_rating.csv')))
    top200_tags = pd.read_csv(join(realpath('top200_tags.csv')))
    top200_movie_genre = pd.read_csv(join(realpath('top200_movie_genre.csv')))
    top070_user_genre = pd.read_csv(join(realpath('top070_user_genre.csv')))

    # 사용자 데이터 추가
    col = ['userId', 'title_only', 'rating']
    top200_movie_rating = top200_movie_rating[col]

    # 선호하는 영화 추가
    tmp = Favorite_movie.query.filter_by(user_id=user_id).all()
    movie_names = []
    for movie in tmp:
        movie_names.append(movie.movie_name)

    # add user data
    for movie_name in movie_names:
        top200_movie_rating = top200_movie_rating.append(
            {'userId': str(user_id), 'title_only': movie_name, 'rating': 5}, ignore_index=True)

    # tag 데이터에서 영화 이름 추출
    # 영화 이름에서 출시일 추출
    top200_tags['movie_year'] = top200_tags['title']
    top200_tags['movie_year'] = top200_tags['movie_year'].str.extract(r"\(([0-9]+)\)", expand=False)

    # 영화 이름에서 이름 추출
    top200_tags['title_only'] = top200_tags['title']
    top200_tags['title_only'] = top200_tags['title_only'].str.extract('(.*?)\s*\(', expand=False)

    # 카운트 추가 / 각 영화 / 각 유저
    top200_tags['count_movie'] = top200_tags.groupby(['movieId', 'tag']).title.transform('count')
    top200_tags['count_user'] = top200_tags.groupby(['userId', 'tag']).title.transform('count')

    top200_tags['rank_movie'] = top200_tags.groupby('movieId')['count_movie'].rank(method='dense', ascending=False)
    top200_tags['rank_user'] = top200_tags.groupby('userId')['count_user'].rank(method='dense', ascending=False)

    # 영화-사용자 가중치 추가
    top200_movie_rating['rank'] = top200_movie_rating['rating'].rank(method='dense', ascending=False)

    # 영화-장르 가중치 추가
    top200_movie_genre['rank'] = 1.0

    # 장르-사용자 가중치 추가
    top070_user_genre['rank'] = top070_user_genre.groupby('userId')['title'].rank(method='dense', ascending=False)

    # 사용자 선호장르 추가
    tmp = User.query.filter_by(id=user_id).all()
    col = ['userId', 'genres_single', 'rank']
    top070_user_genre = top070_user_genre[col]
    for favorite_genre in tmp:
        top070_user_genre = top070_user_genre.append({'userId': str(user_id), 'genres_single': favorite_genre.favorite_genre, 'rank': 1}, ignore_index=True)

    # 그래프 생성
    # 영화-사용자
    g_movie_user = nx.Graph()
    g_movie_user = nx.from_pandas_edgelist(top200_movie_rating, source='title_only', target='userId', edge_attr='rank')

    # 사용자-태그
    g_user_tag = nx.Graph()
    g_user_tag = nx.from_pandas_edgelist(top200_tags, source='userId', target='tag', edge_attr='rank_user')

    # 영화-태그
    g_movie_tag = nx.Graph()
    g_movie_tag = nx.from_pandas_edgelist(top200_tags, source='title_only', target='tag', edge_attr='rank_movie')

    # 영화-장르
    g_movie_genre = nx.Graph()
    g_movie_genre = nx.from_pandas_edgelist(top200_movie_genre, source='title_only', target='genres_single', edge_attr='rank')

    # 사용자-장르
    g_user_genre = nx.Graph()
    g_user_genre = nx.from_pandas_edgelist(top070_user_genre, source='userId', target='genres_single', edge_attr='rank')

    # 그래프 병합
    g_tag_merged = nx.compose(g_user_tag, g_movie_tag)
    g_merged = nx.compose(g_movie_user, g_movie_genre)
    g_merged = nx.compose(g_merged, g_user_genre)
    g_merged = nx.compose(g_merged, g_tag_merged)

    return g_merged












