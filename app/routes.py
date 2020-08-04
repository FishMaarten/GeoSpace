from app import app, db
from app.models import User
from app.forms import LoginForm, GeoForm, RegisterForm
from config import directory
from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from dependencies import GeoTIFF, get_lambert
from random import randint
import plotly.graph_objects as go

@app.route("/login", methods=["GET","POST"])
def login():
    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.validate_on_submit() and login_form.login.data:
        user = User.query.filter_by(username=login_form.username.data).first()
        if user is None or not user.check_password(login_form.password.data):
            return redirect(url_for("login"))
        login_user(user, remember=False)
        return redirect(url_for("index"))
    
    elif register_form.validate_on_submit() and register_form.register.data:
        user = User(
            first_name = register_form.first_name.data,
            last_name = register_form.last_name.data,
            email = register_form.email.data,
            username = register_form.username.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return redirect(url_for("login"))

    return render_template("register.html", title="Register",
            register_form = register_form,
            login_form = login_form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/")
@app.route("/index", methods=["GET","POST"])
@login_required
def index():
    version = randint(0,1000000) 

    if current_user.is_anonymous:
        return redirect(url_for("login"))

    login_form = LoginForm()
    geo_form = GeoForm()

    if login_form.validate_on_submit() and login_form.login.data:
        user = User.query.filter_by(username=login_form.username.data).first()
        if user is None or not user.check_password(login_form.password.data):
            return redirect(url_for("login"))
        login_user(user, remember=False)
        return redirect(url_for("index"))

    elif geo_form.validate_on_submit() and geo_form.plot.data:
        x,y = get_lambert(geo_form.address.data)
        size = int(geo_form.window.data)
        tif = GeoTIFF.get_containing_tif(x,y,size)
        tif = tif.crop_location(x,y,size,size)
        if geo_form.projection.data == "2D": tif.png()
        else:
            xaxis = go.XAxis(range=[0.2,1], showgrid=False, zeroline=False, visible=False)
            yaxis = go.YAxis(range=[0.2,1], showgrid=False, zeroline=False, visible=False)
            layout = go.Layout(
                xaxis = xaxis,
                yaxis = yaxis,
                paper_bgcolor='rgba(0,0,0,0)',
                scene_aspectmode='manual',
                scene_aspectratio=dict(x=1.5, y=1.5, z=0.5),
                margin=dict(l=0, r=0, b=0, t=0))
            fig = go.Figure(data=[go.Surface(z=tif.arr)], layout=layout)
            fig.write_image(directory +"/app/static/plot.png")

    return render_template("geoloc.html", version=version,
            logged = current_user.is_authenticated,
            login_form = login_form,
            geo_form = geo_form)

