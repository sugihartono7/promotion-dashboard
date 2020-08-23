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
from module.ongkir import Ongkir
from werkzeug.exceptions import abort

bp = Blueprint('ongkir', __name__, url_prefix='/back/ongkir')
db = Database()
ongkir = Ongkir()

@bp.route('/get_db_provinces', methods=('GET', 'POST'))
@login_required
def get_db_provinces():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM provinces")
    return json.dumps(cursor.fetchall(), indent=4, sort_keys=True, default=str)

@bp.route('/get_db_cities', methods=('GET', 'POST'))
@login_required
def get_db_cities():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM cities")
    return json.dumps(cursor.fetchall(), indent=4, sort_keys=True, default=str)

@bp.route('/get_db_city_by_province_id', methods=('GET', 'POST'))
@login_required
def get_db_city_by_province_id():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM cities WHERE ro_province_id=%s", (request.args.get('province_id')))
    return json.dumps(cursor.fetchall(), indent=4, sort_keys=True, default=str)

####################### class raja ongkir ###############################
# @bp.route('/get_provinces', methods=('GET', 'POST'))
# @login_required
# def get_provinces():
#     provinces = ongkir.get_provinces()
#     return provinces

# @bp.route('/get_cities_by_province_id', methods=('GET', 'POST'))
# @login_required
# def get_cities_by_province_id():
#     cities = ongkir.get_cities_by_province_id(request.args.get('province_id'))
#     return cities

@bp.route('/get_cost', methods=('GET', 'POST'))
@login_required
def get_cost():
    destination = request.args.get('destination')
    weight = request.args.get('weight')
    cost = ongkir.get_cost(destination, weight)
    return cost