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
from module.form import CustomerVoucerForm
from werkzeug.exceptions import abort

bp = Blueprint('customer_voucer', __name__, url_prefix='/back/customer_voucer')
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
    cursor.execute("SELECT a.*, b.name AS customer_name, c.name AS reward_name FROM customer_voucers a JOIN customers b ON(a.customer_id=b.id) JOIN rewards c ON(c.id=a.reward_id) ")
    customer_voucers = cursor.fetchall()
    return render_template('back/customer_voucer/index.html', customer_voucers=customer_voucers)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    cursor.execute("SELECT * FROM rewards ")
    rewards = cursor.fetchall()

    form = CustomerVoucerForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        reward_id = request.form['reward_id'] or 'NULL'
        voucer_code = request.form['voucer_code'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        is_active = 'is_active' in request.form

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO customer_voucers(customer_id, reward_id, voucer_code, start_date, end_date, is_active) \
                            VALUES(%s, %s, %s, %s, %s, %s)", 
                            (customer_id, reward_id, voucer_code, start_date, end_date, is_active))
            con.commit()
            flash('Operation success')
            return redirect(url_for('customer_voucer.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('customer_voucer.create'))
        finally:
            con.close()
    return render_template('back/customer_voucer/create.html', form=form, customers=customers, rewards=rewards)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customer_voucers WHERE id = %s", (id))
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
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    cursor.execute("SELECT * FROM rewards ")
    rewards = cursor.fetchall()

    form = CustomerVoucerForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        reward_id = request.form['reward_id'] or 'NULL'
        voucer_code = request.form['voucer_code'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        is_active = 'is_active' in request.form

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE customer_voucers \
                                SET customer_id=%s, reward_id=%s, voucer_code=%s, \
                                start_date=%s, end_date=%s, is_active=%s WHERE id=%s", 
                                (customer_id, reward_id, voucer_code, start_date, end_date, is_active, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('customer_voucer.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('customer_voucer.update', id=id))
        finally:
            con.close()
    return render_template('back/customer_voucer/update.html', form=form, data=data, customers=customers, rewards=rewards)  
