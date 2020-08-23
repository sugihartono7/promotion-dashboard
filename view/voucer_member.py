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
from module.form import VoucerMemberForm
from werkzeug.exceptions import abort

bp = Blueprint('voucer_member', __name__, url_prefix='/back/voucer_member')
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
    cursor.execute("SELECT a.*, b.name AS customer_name FROM voucer_members a JOIN customers b ON(a.customer_id=b.id) ")
    voucer_members = cursor.fetchall()
    return render_template('back/voucer_member/index.html', voucer_members=voucer_members)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    form = VoucerMemberForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        percent_discount = request.form['percent_discount'] or 'NULL'
        max_amount = request.form['max_amount'] or 'NULL'
        voucer_code = request.form['voucer_code'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        is_active = 'is_active' in request.form
        created_by = session['user_id'] or 'NULL'

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO voucer_members(customer_id, name, voucer_code, is_active, start_date, end_date, max_amount, percent_discount, created_by) \
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            (customer_id, name, voucer_code, is_active, start_date, end_date, max_amount, percent_discount, created_by))
            con.commit()
            flash('Operation success')
            return redirect(url_for('voucer_member.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('voucer_member.create'))
        finally:
            con.close()
    return render_template('back/voucer_member/create.html', form=form, customers=customers)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM voucer_members WHERE id = %s", (id))
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

    form = VoucerMemberForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        percent_discount = request.form['percent_discount'] or 'NULL'
        max_amount = request.form['max_amount'] or 'NULL'
        voucer_code = request.form['voucer_code'] or 'NULL'
        start_date = request.form['start_date'] or 'NULL'
        end_date = request.form['end_date'] or 'NULL'
        is_active = 'is_active' in request.form
        updated_by = session['user_id'] or 'NULL'

        if is_active == True:
            is_active = 1
        else:
            is_active = 0

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE voucer_members \
                                SET customer_id=%s, name=%s, percent_discount=%s, max_amount=%s, voucer_code=%s, \
                                start_date=%s, end_date=%s, is_active=%s, updated_by=%s WHERE id=%s", 
                                (customer_id, name, percent_discount, max_amount, voucer_code, start_date, end_date, is_active, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('voucer_member.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('voucer_member.update', id=id))
        finally:
            con.close()
    return render_template('back/voucer_member/update.html', form=form, data=data, customers=customers)  
