import functools
import datetime
import json
import http.client
import sys

sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from module.form import SplashScreenForm
from werkzeug.exceptions import abort
from flask import current_app as app
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

bp = Blueprint('splash_screen', __name__, url_prefix='/back/splash_screen')
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[4:5][0]
    return { 'menu' : menu }

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# index
@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM splash_screens ")
    splash_screens = cursor.fetchall()
    return render_template('back/splash_screen/index.html', splash_screens=splash_screens)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = SplashScreenForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        photo = request.files['photo']
        is_active = 'is_active' in request.form
        file_url = ""

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        if photo.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if photo and allowed_file(photo.filename):
            photos = UploadSet('photos', IMAGES)
            configure_uploads(app, photos)
            filename = photos.save(request.files['photo'])
            file_url = photos.url(filename)

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO splash_screens(name, photo, is_active) VALUES(%s, %s, %s)", (name, file_url, is_active))
            con.commit()
            flash('Operation success')
            return redirect(url_for('splash_screen.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('splash_screen.create'))
        finally:
            con.close()
    return render_template('back/splash_screen/create.html', form=form)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM splash_screens WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)

    form = SplashScreenForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        photo = request.files['photo']
        is_active = 'is_active' in request.form
        file_url = ""

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)

        if photo and allowed_file(photo.filename):
            photos = UploadSet('photos', IMAGES)
            configure_uploads(app, photos)
            filename = photos.save(request.files['photo'])
            file_url = photos.url(filename)

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE splash_screens SET name=%s, photo=%s, is_active=%s WHERE id=%s", (name, file_url, is_active, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('splash_screen.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('splash_screen.update', id=id))
        finally:
            con.close()
    return render_template('back/splash_screen/update.html', form=form, data=data)  
