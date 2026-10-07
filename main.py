from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

movies_api_key = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1NGQ5MTY1ZjI0MmJlYzU2NzNiZDlkZDg3ZDQ4OTgwMiIsInN1YiI6IjY0ZmEyYTA5ZGI0ZWQ2MDBjNDM3MGM5OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bjb_N-Ojb7YtAyTvNGgvbqYin4k6MaORZdsu3ZjRktU"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy()
db.init_app(app)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    title = db.Column(db.String, unique = True, nullable = False)
    year = db.Column(db.Integer, nullable = False)
    description = db.Column(db.String, nullable = False)
    rating = db.Column(db.Integer, nullable = True)
    ranking = db.Column(db.Integer, nullable = True)
    review = db.Column(db.String, nullable = True)
    img_url = db.Column(db.String, nullable = False)

class Edit_form(FlaskForm):
    new_rating = StringField('Your rating out of 10 - e.g. 9.6', validators=[DataRequired()])
    new_review = StringField('Your review', validators=[DataRequired()])
    button = SubmitField('Done')

class Add_movie(FlaskForm):
    movie_title = StringField(validators=[DataRequired()])
    add_button = SubmitField('Add Movie')

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movies).order_by(Movies.rating))
        all_movies = result.scalars().all()
        x = len(all_movies)
        for movie in all_movies:
            movie.ranking = x
            x -= 1 
    return render_template("index.html", movies = all_movies)

@app.route("/update", methods = ["GET", "POST"])
def update():
    form = Edit_form()
    id = request.args.get('id')
    name = request.args.get('name')
    if form.validate_on_submit():
        with app.app_context():
            movie_to_update = db.get_or_404(Movies, id)
            movie_to_update.rating = form.new_rating.data
            movie_to_update.review = form.new_review.data
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form = form, title = name)

@app.route("/delete/<int:id>")
def delete(id):
    with app.app_context():
        movie_to_delete = db.get_or_404(Movies, id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods = ['GET','POST'])
def add():
    add_form = Add_movie()
    if add_form.validate_on_submit():
        header = {
            "Authorization": f"Bearer {movies_api_key}",
        }
        parameters ={
            'query': add_form.movie_title.data
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params =parameters, headers = header)
        response.raise_for_status()
        data = response.json()['results']
        return render_template('select.html', data = data)
    return render_template('add.html', form = add_form)

@app.route("/details")
def details():
    movie_id = request.args.get('id')
    header = {
            "Authorization": f"Bearer {movies_api_key}",
        }
    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", headers=header)
    response.raise_for_status()
    movie_data = response.json()
    new_movie = Movies(title = movie_data['original_title'], year = movie_data['release_date'].split('-')[0], description = movie_data['overview'], img_url = f"https://www.themoviedb.org/t/p/original{movie_data['poster_path']}", ranking = "None", review = "None", rating = "None")
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('update', id = new_movie.id, name = new_movie.title))



if __name__ == '__main__':
    app.run(debug=True)
