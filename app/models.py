from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(), nullable=False)
    favorite_genre = db.Column(db.Text(), nullable=True)
    unfavorite_genre = db.Column(db.Text(), nullable=True)
    create_date = db.Column(db.DateTime(), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(), nullable=False)
    link_id = db.Column(db.Integer, nullable=False)
    genres = db.Column(db.Text(), nullable=False)

class Favorite_movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id', ondelete='CASCADE'))
    movie_name = db.Column(db.Text(), db.ForeignKey('movie.name', ondelete='CASCADE'))
    create_date = db.Column(db.DateTime(), nullable=False)

class Recommended_movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id', ondelete='CASCADE'))
    movie_name = db.Column(db.Text(), db.ForeignKey('movie.name', ondelete='CASCADE'))
    predicted_rating = db.Column(db.Integer(), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('movie.link_id', ondelete='CASCADE'))
    genres = db.Column(db.Text(), db.ForeignKey('movie.genres', ondelete='CASCADE'))
    create_date = db.Column(db.DateTime(), nullable=False)


