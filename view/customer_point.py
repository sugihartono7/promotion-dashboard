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

bp = Blueprint('customer_point', __name__, url_prefix='/back/customer_point')
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
    cursor.execute("SELECT a.id, a.name AS customer_name, c.name AS customer_class_name, \
                    SUM(b.point) AS total_point \
                    FROM customers a JOIN customer_points b ON(a.id=b.customer_id) \
                    JOIN customer_classes c ON(c.id=a.customer_class_id) \
                    GROUP BY a.id, a.name, c.name")
    customer_points = cursor.fetchall()
    return render_template('back/customer_point/index.html', customer_points=customer_points)

@bp.route('/<int:id>/history', methods=('GET', 'POST'))
@login_required
def history(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.name AS customer_name, b.* FROM customers a JOIN customer_points b ON(a.id=b.customer_id)")
    customer_points = cursor.fetchall()

    cursor.execute("SELECT name FROM customers WHERE id=%s", (id))
    customer = cursor.fetchone()
    return render_template('back/customer_point/history.html', customer_points=customer_points, customer=customer)

