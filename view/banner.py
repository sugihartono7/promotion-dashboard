import functools
import datetime
import json
import http.client
import os
import sys
from .auth import login_required
sys.path.append("..")

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from module.form import BannerForm

from werkzeug.exceptions import abort
from flask import current_app as app
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

bp = Blueprint('banner', __name__, url_prefix='/back/banner')
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
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name AS product_name FROM banners a JOIN products b ON(a.product_id=b.id)")
    banners = cursor.fetchall()
    return render_template('back/banner/index.html', banners=banners)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    form = BannerForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        product_id = request.form['product_id'] or 'NULL'
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
            cursor.execute("INSERT INTO banners(name, photo, is_active, product_id) VALUES(%s, %s, %s, %s)", (name, file_url, is_active, product_id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('banner.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('banner.create'))
        finally:
            con.close()
    return render_template('back/banner/create.html', form=form, products=products)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM banners WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    form = BannerForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        product_id = request.form['product_id'] or 'NULL'
        photo = request.files['photo']
        is_active = 'is_active' in request.form
        file_url = ""

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        if photo and allowed_file(photo.filename):
            photos = UploadSet('photos', IMAGES)
            configure_uploads(app, photos)
            filename = photos.save(request.files['photo'])
            file_url = photos.url(filename)

        try:
            if photo.filename == '':
                cursor.execute("UPDATE banners SET name=%s, is_active=%s, product_id=%s WHERE id=%s", (name, is_active, product_id, id))
            else:
                cursor.execute("UPDATE banners SET name=%s, photo=%s, is_active=%s, product_id=%s WHERE id=%s", (name, file_url, is_active, product_id, id))

            con.commit()
            flash('Operation success')
            return redirect(url_for('banner.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('banner.update', id=id))
        finally:
            con.close()

    return render_template('back/banner/update.html', form=form, data=data, products=products)  
