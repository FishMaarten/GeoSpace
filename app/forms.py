from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, SelectField)
from wtforms.validators import DataRequired, ValidationError, EqualTo

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Log In")

class GeoForm(FlaskForm):
    WINDOWS = [("50","50x50"),("80","80x80"),("100","100x100"),("140","140x140")]
    PROJECTION = [("2D","2D Projection ( x , y )"), ("3D","3D Projection ( x , y , z )")]
    header = "Plot any building in Flanders!"
    address = StringField("Which address would you like to see?", validators=[DataRequired()])
    projection = SelectField("Projection", choices=PROJECTION, validators=[DataRequired()])
    surroundings = BooleanField("View surroundings?")
    window = SelectField("Window size", choices=WINDOWS, validators=[DataRequired()])
    plot = SubmitField("Plot")

class RegisterForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email-Address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Re-enter Password", validators=[DataRequired()])
    register = SubmitField("Register")

    def validate_username(self, username):
        print("validusername")
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Username already in use")
    def validate_email(self, email):
        print("validemail")
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Email already in use")
