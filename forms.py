from flask_wtf import Form
from flask_wtf.file import FileField

from wtforms import StringField, PasswordField, TextAreaField, FileField
import wtforms

from wtforms.validators import (
    DataRequired,
    Regexp,
    ValidationError,
    Email,
    Length,
    EqualTo,
)

from models import User


def name_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError("User with this name already exists.")


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError("User with this email already exists.")


class RegisterForm(Form):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z0-9_]+$",
                message=(
                    "Username should be one word, letters, numbers and underscores only."
                ),
            ),
            name_exists,
        ],
    )

    email = StringField("Email", validators=[DataRequired(), Email(), email_exists])

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=2),
            EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm Password", validators=[DataRequired()])
    photo = FileField('Your photo')


class LoginForm(Form):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class PostForm(Form):
    name = TextAreaField("Project name")
    content = TextAreaField("Project description", validators=[DataRequired()])
