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
from module.form import CustomerClassForm
from werkzeug.exceptions import abort

bp = Blueprint('customer_class', __name__, url_prefix='/back/customer_class')
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
    cursor.execute("SELECT * FROM customer_classes ")
    customer_classes = cursor.fetchall()
    return render_template('back/customer_class/index.html', customer_classes=customer_classes)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CustomerClassForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form['code'] or 'NULL'
        name = request.form['name'] or 'NULL'
        percent_discount = request.form['percent_discount'] or 'NULL'
        first_transaction = request.form['first_transaction'] or 'NULL'
        next_transaction = request.form['next_transaction'] or 'NULL'
        created_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO \
                            customer_classes( \
                                code, name, percent_discount, first_transaction, next_transaction, created_by \
                            ) VALUES(%s, %s, %s, %s, %s, %s)", 
                            (code, name, percent_discount, first_transaction, next_transaction, created_by)
                        )
            con.commit()
            flash('Operation success')
            return redirect(url_for('customer_class.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('customer_class.create'))
        finally:
            con.close()
    return render_template('back/customer_class/create.html', form=form)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customer_classes WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)

    form = CustomerClassForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form['code'] or 'NULL'
        name = request.form['name'] or 'NULL'
        percent_discount = request.form['percent_discount'] or 'NULL'
        first_transaction = request.form['first_transaction'] or 'NULL'
        next_transaction = request.form['next_transaction'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE customer_classes SET \
                            code=%s, name=%s, percent_discount=%s, first_transaction=%s, \
                            next_transaction=%s, updated_by=%s  WHERE id=%s",
                            (code, name, percent_discount, first_transaction, next_transaction, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('customer_class.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('customer_class.update', id=id))
        finally:
            con.close()
            
    return render_template('back/customer_class/update.html', form=form, data=data)  
