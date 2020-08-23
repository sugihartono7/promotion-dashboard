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
from module.form import PromotionForm
from werkzeug.exceptions import abort

bp = Blueprint('promotion', __name__, url_prefix='/back/promotion')
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
    cursor.execute("SELECT * FROM promotions ")
    promotions = cursor.fetchall()
    return render_template('back/promotion/index.html', promotions=promotions)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = PromotionForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        info = request.form['info'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        created_by = session['user_id'] or 'NULL'

        # return datetime.datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d")
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO promotions(name, info, start_date, end_date, created_by) \
                            VALUES(%s, %s, %s, %s, %s)", 
                            (name, info, start_date, end_date, created_by))
            con.commit()
            flash('Operation success')
            return redirect(url_for('promotion.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('promotion.create'))
        finally:
            con.close()
    return render_template('back/promotion/create.html', form=form)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM promotions WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)

    form = PromotionForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form['name'] or 'NULL'
        info = request.form['info'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE promotions \
                                SET name=%s, info=%s, start_date=%s, end_date=%s, updated_by=%s WHERE id=%s", 
                                (name, info, start_date, end_date, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('promotion.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('promotion.update', id=id))
        finally:
            con.close()
    return render_template('back/promotion/update.html', form=form, data=data)  
