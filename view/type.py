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
from module.form import TypeForm
from werkzeug.exceptions import abort

bp = Blueprint('type', __name__, url_prefix='/back/type')
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[4:5][0]
    return { 'menu' : menu }

# index
@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM types")
    types = cursor.fetchall()
    return render_template('back/type/index.html', types=types)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = TypeForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        created_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO types(name, created_by) VALUES(%s, %s)", (name, created_by))
            con.commit()
            flash('Operation success')
            return redirect(url_for('type.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('type.create'))
        finally:
            con.close()
    return render_template('back/type/create.html', form=form)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM types WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)

    form = TypeForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE types SET name=%s, updated_by=%s WHERE id=%s", (name, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('type.update', id=id))
        except:
            con.rollback()
            return redirect(url_for('type.update', id=id))
        finally:
            con.close()
    return render_template('back/type/update.html', form=form, data=data)  
