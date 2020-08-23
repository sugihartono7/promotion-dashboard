import functools
import datetime
import json
import http.client
import os
import sys

sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from module.form import RewardForm
from werkzeug.exceptions import abort
from flask import current_app as app
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

bp = Blueprint('reward', __name__, url_prefix='/back/reward')
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[4:5][0]
    return { 'menu' : menu }

@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name AS promotion_name FROM rewards a JOIN promotions b on(a.promotion_id=b.id)")
    rewards = cursor.fetchall()
    return render_template('back/reward/index.html', rewards=rewards)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM promotions")
    promotions = cursor.fetchall()
    
    form = RewardForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        promotion_id = request.form['promotion_id'] or 'NULL'
        name = request.form['name']
        info = request.form['info'] or 'NULL'
        point = request.form['point'] or 'NULL'
        value = request.form['value'] or 'NULL'
        type = request.form['type'] or 'NULL'
        created_by = session['user_id'] or 'NULL'
        photo = request.files['photo']
        file_url = ""

        if photo and allowed_file(photo.filename):
            photos = UploadSet('photos', IMAGES)
            configure_uploads(app, photos)
            filename = photos.save(request.files['photo'])
            file_url = photos.url(filename)

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO \
                            rewards( \
                                promotion_id, name, info,\
                                point, value, created_by, type, path \
                            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                            (promotion_id, name, info, point, value, created_by, type, file_url)
                        )
            con.commit()
            flash('Operation success')
            return redirect(url_for('reward.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('reward.create'))
        finally:
            con.close()
    return render_template('back/reward/create.html', form=form, promotions=promotions)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM rewards WHERE id = %s", (id))
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
    cursor.execute("SELECT * FROM promotions")
    promotions = cursor.fetchall()

    form = RewardForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        promotion_id = request.form['promotion_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        info = request.form['info'] or 'NULL'
        point = request.form['point'] or 'NULL'
        value = request.form['value'] or 'NULL'
        type = request.form['type'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        photo = request.files['photo']
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            if 'photo' not in request.files:
                cursor.execute("UPDATE rewards SET \
                                promotion_id=%s, name=%s, info=%s, \
                                point=%s, value=%s, updated_by=%s, type=%s \
                                WHERE id=%s",
                                (promotion_id, name, info, point, value, updated_by, type, id))
            else:
                if photo and allowed_file(photo.filename):
                    photos = UploadSet('photos', IMAGES)
                    configure_uploads(app, photos)
                    filename = photos.save(request.files['photo'])
                    file_url = photos.url(filename)

                cursor.execute("UPDATE rewards SET \
                                promotion_id=%s, name=%s, info=%s, \
                                point=%s, value=%s, updated_by=%s, type=%s, path=%s \
                                WHERE id=%s",
                                (promotion_id, name, info, point, value, updated_by, type, file_url, id))

            con.commit()
            flash('Operation success')
            return redirect(url_for('reward.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('reward.update', id=id))
        finally:
            con.close()
            
    return render_template('back/reward/update.html', form=form, data=data, promotions=promotions)  
