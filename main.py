from security.const import *
from forms.forms import *
from data import db_session
from data.users import Users
import films_resource
import users_resource

import requests
import json
from werkzeug.security import generate_password_hash
from flask_recaptcha import ReCaptcha
from flask_restful import Api
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_mail import Mail, Message
from flask import Flask, render_template, redirect
from wtforms.fields.html5 import EmailField
from wtforms.fields import StringField, PasswordField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['RECAPTCHA_SITE_KEY'] = RECAPTCHA_SITE_KEY
app.config['RECAPTCHA_SECRET_KEY'] = RECAPTCHA_SECRET_KEY
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

mail = Mail(app)

recaptcha = ReCaptcha(app=app)

api = Api(app)
api.add_resource(films_resource.FilmsListResource, '/api/films/<token>')
api.add_resource(films_resource.FilmsResource, '/api/films/<token>/<int:films_id>')
api.add_resource(users_resource.UsersListResource, '/api/users/<token>')
api.add_resource(users_resource.UsersResource, '/api/users/<token>/<int:users_id>')

login_manager = LoginManager()
login_manager.init_app(app)


def send_email_to(recipients, text="Test"):
    msg = Message(text, sender=FULL_MAIL_USERNAME, recipients=recipients)
    mail.send(msg)
    return 'success'


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(Users).get(user_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template("base.html")


# Done
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        users = session.query(Users).filter(Users.email == form.email.data).first()
        if users and users.check_password(form.password.data):
            login_user(users, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template("login.html", form=form)


# Done
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if not recaptcha.verify():
            message = "Подтвердите что вы не робот"
            return render_template("register.html", form=form, message=message)
        else:
            not_hash = gen_password()
            password = generate_password_hash(not_hash)
            params = {
                'nickname': form.username.data,
                'email': form.email.data,
                'hashed_password': password,
                'access_level': 1
            }
            info = json.loads(requests.post("http://localhost:5000/api/users/" + TOKEN, json=params).content)
            message = ""
            for key in info:
                message += str(info[key]) + "\n"
            if 'success' in info:
                send_email_to([form.email.data], "Ваш пароль от сайта: {}".format(not_hash))
            return render_template("register.html", form=form, message=message)
    return render_template("register.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/film_page/<int:film_id>")
def film_page(film_id):
    film_info = {
        'photo_url': 'https://upload.wikimedia.org/wikipedia/ru/thumb/9/93/Pulp_Fiction.jpg/211px-Pulp_Fiction.jpg',
        'title': 'title',
        'year': 'year',
        'country': 'country',
        'genre': 'genre',
        'duration': 'duration',
        'description': 'description',
        'score': 10,
        'year_war': 16,
        'film_url': 'https://stonehenge.load.hdrezka-ag.net/tvseries/f455776e70b462a514403e5dae056fc894ca5c92/a2b31d7e35a4d1a4bb024721e145d494:2020042511/240.mp4'
    }
    return render_template("film_page.html", film=film_info)


@app.route("/add_film", methods=['GET', 'POST'])
def add_film():
    form = AddFilmForm()
    if form.validate_on_submit() and recaptcha.verify():
        params = {
            'title': form.title.data,
            'year': form.year.data,
            'country': form.country.data,
            'genre': form.genre.data,
            'age': form.age.data,
            'description': form.description.data,
            'show': form.show.data,
            'film_url': form.film_url.data,
            'photo_url': form.photo_url.data,
            'score': form.score.data
        }
        info = json.loads(requests.post("http://localhost:5000/api/films/" + TOKEN, json=params).content)
        message = ""
        for key in info:
            message += str(info[key]) + "\n"
        return render_template("add_film.html", form=form, message=message)
    return render_template("add_film.html", form=form)


if __name__ == '__main__':
    db_session.global_init("db/data.sqlite")
    app.run()