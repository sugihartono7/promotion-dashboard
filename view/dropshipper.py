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
from module.form import DropshipperForm
from werkzeug.exceptions import abort

bp = Blueprint('dropshipper', __name__, url_prefix='/back/dropshipper')
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
    cursor.execute("SELECT b.*, a.name as customer_name FROM customers a JOIN dropshipper_childs b ON(a.id=b.customer_id)")
    dropshippers = cursor.fetchall()
    return render_template('back/dropshipper/index.html', dropshippers=dropshippers)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT id, name FROM customers WHERE customer_class_id=2")
    customers = cursor.fetchall()
    
    form = DropshipperForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        address = request.form['address'] or 'NULL'
        phone = request.form['phone'] or 'NULL'
        created_by = session['user_id'] or 'NULL'
        province_id = request.form['province_id'] or 'NULL'
        city_id = request.form['city_id'] or 'NULL'
        # subdistrict_id = request.form['subdistrict_id'] or 'NULL'
        postal_code = request.form['postal_code'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO \
                            dropshipper_childs( \
                                customer_id, name, address, \
                                province_id, city_id, postal_code, phone, \
                                created_by \
                            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                            (customer_id, name, address, province_id, city_id, 
                            postal_code, phone, created_by)
                        )
            con.commit()
            flash('Operation success')
            return redirect(url_for('dropshipper.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('dropshipper.create'))
        finally:
            con.close()
    return render_template('back/dropshipper/create.html', form=form, customers=customers)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM dropshipper_childs WHERE id = %s", (id))
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
    cursor.execute("SELECT id, name FROM customers WHERE customer_class_id=2")
    customers = cursor.fetchall()

    form = DropshipperForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        address = request.form['address'] or 'NULL'
        phone = request.form['phone'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        province_id = request.form['province_id'] or 'NULL'
        city_id = request.form['city_id'] or 'NULL'
        # subdistrict_id = request.form['subdistrict_id'] or 'NULL'
        postal_code = request.form['postal_code'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE dropshipper_childs SET \
                            customer_id=%s, name=%s, address=%s, \
                            phone=%s, updated_by=%s, province_id=%s, \
                            city_id=%s, postal_code=%s, updated_by=%s \
                            WHERE id=%s",
                            (customer_id, name, address, phone, updated_by, province_id, city_id, postal_code, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('dropshipper.update', id=id))
        except:
            con.rollback()
            return redirect(url_for('dropshipper.update', id=id))
        finally:
            con.close()
    return render_template('back/dropshipper/update.html', form=form, data=data, customers=customers)  
