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
from werkzeug.security import check_password_hash, generate_password_hash
from module.database import Database
from werkzeug.exceptions import abort

bp = Blueprint('popular', __name__, url_prefix='/back/popular')
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
    cursor.execute("SELECT a.name, b.is_active, b.id FROM products a JOIN populars b ON(a.id=b.product_id) ")
    populars = cursor.fetchall()
    return render_template('back/popular/index.html', populars=populars)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    if request.method == 'POST' :
        product_id = request.form['product_id'] or 'NULL'
        is_active = 'is_active' in request.form

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO populars(product_id, is_active) \
                            VALUES(%s, %s)", 
                            (product_id, is_active))
            con.commit()
            flash('Operation success')
            return redirect(url_for('popular.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('popular.create'))
        finally:
            con.close()
    return render_template('back/popular/create.html', products=products)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM populars WHERE id = %s", (id))
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
    cursor.execute("SELECT * FROM products ")
    products = cursor.fetchall()

    if request.method == 'POST' :
        product_id = request.form['product_id'] or 'NULL'
        is_active = 'is_active' in request.form

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE populars \
                                SET product_id=%s, is_active=%s WHERE id=%s", 
                                (product_id, is_active, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('popular.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('popular.update', id=id))
        finally:
            con.close()
    return render_template('back/popular/update.html', data=data, products=products)  
