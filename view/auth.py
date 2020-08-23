import functools
import datetime
import sys

sys.path.append("..")

from flask import (
    Blueprint, flash, redirect, g, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from module.database import Database
import psycopg2.extras

bp = Blueprint('auth', __name__, url_prefix='/')
db = Database()

# login
@bp.route('/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])
        error = None
        
        con = db.connect()
        cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role_id'] = user['role_id']
            return  redirect(url_for('dashboard.index'))
        flash(error)
    return render_template('auth/login.html')
    
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        con = db.connect()
        cursor = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        g.user = cursor.fetchone()
    
@bp.route('/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
    