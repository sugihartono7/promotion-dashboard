import functools
import datetime
import json
import http.client
import sys
import os

sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from module.database import Database
from module.form import UserForm
from werkzeug.exceptions import abort
import psycopg2.extras

import json
import plotly
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import csv
pd.options.display.max_columns = None

from flask import current_app as app

bp = Blueprint('user', __name__, url_prefix='/user')
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
    cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)    
    cursor.execute("SELECT * FROM users WHERE role_id !=4")
    users = cursor.fetchall()
    
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape', dtype={'store_code':'str'})
    stores = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA'].sort_values(by=['initial'], ascending=True).to_dict('records')
    directorates = pd.read_csv('/app/data/master/directorate_huruf', sep=',', encoding='unicode_escape')
    directorates = directorates.groupby(['dirdesc']).sum().reset_index().to_dict('records')
    divisions = []

    start_date = ""
    end_date = ""
    store = ""
    directorate = ""
    division = ""
    category = ""

    filenames = []
    for filename in os.listdir("/app/data/upload"):
        filenames.append(filename)

    return render_template(
        'user/index.html', users=users, 
        stores = stores, directorates = directorates, divisions = divisions,
        _start_date = start_date, _end_date = end_date, _store = store,
        _directorate = directorate, _division = division, _category = category,
        filenames = filenames
    )

@bp.route('/changepass', methods=('GET', 'POST'))
@login_required
def changepass():
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape', dtype={'store_code':'str'})
    stores = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA'].sort_values(by=['initial'], ascending=True).to_dict('records')
    directorates = pd.read_csv('/app/data/master/directorate_huruf', sep=',', encoding='unicode_escape')
    directorates = directorates.groupby(['dirdesc']).sum().reset_index().to_dict('records')
    divisions = []

    start_date = ""
    end_date = ""
    store = ""
    directorate = ""
    division = ""
    category = ""

    filenames = []
    for filename in os.listdir("/app/data/upload"):
        filenames.append(filename)

    if request.method == 'POST':
        old_password = request.form['old_password'] or 'NULL'
        new_password = request.form['new_password'] or 'NULL'

        data = get_data(session['username'])
        if not check_password_hash(data['password'], old_password):
            flash('Old Password mismatch')
            return redirect(url_for('user.changepass'))

        try:
            con = db.connect()
            cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("UPDATE users SET password = %s WHERE username=%s", (generate_password_hash(new_password), session['username'],))
            con.commit()
            flash('Operation success')
            return redirect(url_for('user.changepass'))
        except psycopg2.Error as e:
            con.rollback()
            flash(e)
            return redirect(url_for('user.changepass'))
        finally:
            con.close()

    return render_template(
        'user/changepass.html',
        stores = stores, directorates = directorates, divisions = divisions,
        _start_date = start_date, _end_date = end_date, _store = store,
        _directorate = directorate, _division = division, _category = category,
        filenames = filenames
    )

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        full_name = request.form['full_name'] or 'NULL'
        username = request.form['username'] or 'NULL'
        role_id = 8 
        password = username
        email = "user@demo.com"
        created_by = session['user_id'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        is_suspended = 0
        is_disabled = 0
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%m:%S')

        if username_exists(username) == '1':
            flash('Username is exists, try another username')
            return redirect(url_for('user.create'))

        try:
            con = db.connect()
            cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("INSERT INTO users \
                (full_name, username, email, role_id, password, \
                is_suspended, is_disabled, created_by, updated_by, created_at, updated_at) \
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                (full_name, username, email, role_id, generate_password_hash(password), is_suspended, is_disabled, created_by, updated_by, now, now))
            
            con.commit()
            flash('Operation success')
            return redirect(url_for('user.create'))
        except psycopg2.Error as e:
            con.rollback()
            flash(e)
            return redirect(url_for('user.create'))
        finally:
            con.close()
    return render_template('user/create.html')    

def get_data(username):
    con = db.connect()
    cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data username {0} doesn't exist.".format(username))

    return data

def username_exists(username):
    con = db.connect()
    cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    data = cursor.fetchone()
    if data is None:
        return '0'
    else:
        return '1'

@bp.route('/<string:username>/update', methods=('GET', 'POST'))
@login_required
def update(username):
    data = get_data(username)

    if request.method == 'POST':
        id = request.form['id'] or 'NULL'
        full_name = request.form['full_name'] or 'NULL'
        username = request.form['username'] or 'NULL'
        password = request.form['password'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%m:%S')
        
        try:
            con = db.connect()
            cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if password is None:
                cursor.execute("UPDATE users \
                                    SET full_name=%s, updated_by=%s WHERE id=%s", 
                                    (full_name, updated_by, id))
            else:
                cursor.execute("UPDATE users \
                                    SET full_name=%s, password=%s, updated_by=%s WHERE id=%s", 
                                    (full_name, generate_password_hash(password), updated_by, id))
                
            con.commit()
            flash('Operation success')
            return redirect(url_for('user.update', username=username))
        except psycopg2.Error as e:
            con.rollback()
            flash(e)
            return redirect(url_for('user.update', username=username))
        finally:
            con.close()
    return render_template('user/update.html', data=data)  
