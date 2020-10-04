from flask import Flask, g, render_template, flash, redirect, url_for, abort, request
from flask_bcrypt import check_password_hash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import numpy as np

import uuid
import forms
import models

DEBUG = True
PORT = 80
HOST = "0.0.0.0"

app = Flask(__name__)
app.secret_key = "asdnafnj#46sjsnvd(*$43sfjkndkjvnskb6441531@#$$6sddf"
"""here secret_key is a random string of alphanumerics"""

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to database before each request
    g is a global object, passed around all time in flask, used to setup things which
    we wanna have available everywhere.
    """
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """close all database connection after each request"""
    g.db.close()
    return response


@app.route("/register", methods=("GET", "POST"))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("Congrats, Registered Successfully!", "success")
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            photo=form.photo.data,
        )
        return redirect(url_for("index"))
    return render_template("register.html", form=form)


@app.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password does not match", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                """Creating a session on user's browser"""
                flash("You have been logged in", "success")
                return redirect(url_for("index"))
            else:
                flash("Your email or password does not match", "error")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/new_post", methods=("GET", "POST"))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Project.create_project(
            from_user=g.user.id,
            description=form.content.data.strip(),
            project_id=np.random.randint(0, 100000),
            name=form.name.data.strip()
        )
        flash("Message Posted: Thanks!", "success")
        return redirect(url_for("index"))
    return render_template("post.html", form=form)


@app.route("/stream")
@app.route("/stream/<username>")
def stream(username=None):
    template = "stream.html"
    if username and (current_user.is_anonymous or username != current_user.username):
        try:
            user = models.User.select().where(models.User.username ** username).get()
        except models.DoesNotExist:
            abort(404)
        else:
            stream = user.posts.limit(100)
    else:
        stream = current_user.get_stream().limit(100)
        user = current_user
    if username:
        template = "user_stream.html"
    return render_template(template, stream=stream, user=user)


@app.route("/post/<int:post_id>")
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template("stream.html", stream=posts)


@app.route("/follow/<username>")
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(), to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You are now following {}".format(to_user.username), "success")
    return redirect(url_for("stream", username=to_user.username))


@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(), to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You have unfollowed {}".format(to_user.username), "success")
    return redirect(url_for("stream", username=to_user.username))


@app.route("/ideas")
def view_idea():
    data = request.args
    idea_id = data.get('idea_id', None)
    project_id = data.get('project_id', None)
    ideas = None
    if idea_id is not None:
        ideas = models.Idea.select().where(models.Idea.id == idea_id)
    if project_id is not None:
        if ideas is not None:
            ideas = ideas.where(models.Idea.for_project == project_id)
        else:
            ideas = models.Idea.select().where(models.Idea.for_project == project_id)
    if ideas.count() == 0:
        abort(404)
    return render_template("ideas.html", stream=ideas)


@app.route("/project/<int:project_id>")
def view_project(project_id):
    posts = models.Project.select().where(models.Project.project_id == project_id)
    if posts.count() == 0:
        abort(404)
    return render_template("project.html", stream=posts)

@app.route("/qa")
def view_qa():
    data = request.args
    project_id = data.get("project_id", None)
    posts = models.Project.select().where(models.Project.project_id == project_id)
    return render_template("qa.html", stream=posts)

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.route("/")
def index():
    stream = models.Project.select().limit(100)
    return render_template("stream.html", stream=stream)


@app.route("/people")
def get_people():
    return render_template("people.html")


if __name__ == "__main__":
    models.initialize()
    models.Project.create_project(
        1,
        "This is my first project description",
        "2",
        "First project ever"
    )

    models.Project.create_project(
        2,
        "This is my second project description",
        "2",
        "Second project ever"
    )
    models.Idea.create_idea(1, 's', 'This is my first idea', 1, 'Idea #1')
    app.run(debug=DEBUG, host=HOST, port=PORT)
