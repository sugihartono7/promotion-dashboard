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
from werkzeug.exceptions import abort

bp = Blueprint('sales', __name__, url_prefix='/back/sales')
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
    cursor.execute("SELECT a.id, a.created_at, a.code, a.status_trans, \
                    CONCAT(b.bank_name, ' ', b.bank_number) AS bank_info, a.shipment_phone, \
                    (a.gross_total + a.shipment_fee - a.discount_voucer_ongkir - a.discount_voucer) AS total, \
                    b.name AS customer_name \
                    FROM online_sales a JOIN customers b ON(a.customer_id=b.id) \
                    WHERE a.is_cart != 1")
    sales = cursor.fetchall()
    return render_template('back/sales/index.html', sales=sales)

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customers WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    online_sales_id = id
    code = ""
    tanggal = ""
    status_trans = ""
    shipment_fee = None
    shipment_service = ""
    province_name = ""
    city_name = ""
    info = ""
    shipment_name = ""
    shipment_address = ""
    shipment_phone = ""
    postal_code = ""
    product_name = ""
    discount_voucer = 0
    discount_voucer_ongkir = 0

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.*, c.name AS product_name, c.sku, \
                    c.weight, a.code, a.created_at AS tanggal, a.status_trans, a.shipment_no, \
                    a.info, a.shipment_service, a.shipment_name, a.shipment_address, a.postal_code, a.shipment_phone, \
                    a.shipment_fee, d.ro_province AS province_name, a.customer_id, \
                    a.discount_voucer, a.discount_voucer_ongkir, a.voucer_code, \
                    CONCAT(e.ro_type, ' ', e.ro_city_name) AS city_name \
                    FROM online_sales a JOIN online_sales_details b ON(a.id=b.online_sales_id) \
                    JOIN products c ON(c.id=b.product_id) \
                    JOIN provinces d ON(d.ro_province_id=a.province_id)    \
                    JOIN cities e ON(e.ro_city_id=a.city_id)    \
                    WHERE a.id=%s", (id))
    products = cursor.fetchall()

    if (cursor.rowcount >= 1):
        online_sales_id = products[0]['online_sales_id'] 
        code = products[0]['code'] 
        tanggal = products[0]['tanggal'] 
        status_trans = products[0]['status_trans'] 
        shipment_no = products[0]['shipment_no'] 
        shipment_fee = products[0]['shipment_fee'] 
        shipment_service = products[0]['shipment_service'] 
        province_name = products[0]['province_name'] 
        city_name = products[0]['city_name'] 
        info = products[0]['info'] 
        shipment_name = products[0]['shipment_name'] 
        shipment_address = products[0]['shipment_address'] 
        postal_code = products[0]['postal_code'] 
        product_name = products[0]['product_name'] 
        shipment_phone = products[0]['shipment_phone'] 
        customer_id = products[0]['customer_id'] 
        discount_voucer = products[0]['discount_voucer'] 
        discount_voucer_ongkir = products[0]['discount_voucer_ongkir'] 
        voucer_code = products[0]['voucer_code'] 
    
    cursor.execute("SELECT c.id, SUM(a.weight) AS weight_total, SUM(b.sell_price * b.qty) AS total, \
                    SUM(b.point) AS point_total \
                    FROM products a JOIN online_sales_details b ON(a.id=b.product_id) \
                    JOIN online_sales c ON(c.id=b.online_sales_id) \
                    WHERE c.id=%s GROUP BY c.id", (id))
                    
    total = cursor.fetchone()
    weight_total = total['weight_total']
    point_total = total['point_total']
    total = total['total']
    info_cust_point = "Transaksi Belanja #"+code

    if request.method == 'POST':
        status_trans = request.form['status_trans']
        shipment_no = request.form['shipment_no']
        updated_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        updated_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE online_sales SET \
                            status_trans=%s, updated_at=%s, shipment_no=%s \
                            WHERE id=%s",
                            (status_trans, updated_at, shipment_no, id))
            
            if status_trans == "Transaksi Selesai":
                cursor.execute("INSERT INTO  customer_points(info, point, customer_id) VALUES(%s, %s, %s)", (info_cust_point, point_total, customer_id))  

            con.commit()
            flash('Operation success')
            return redirect(url_for('sales.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('sales.update', id=id))
        finally:
            con.close()
            
    return render_template('back/sales/update.html', voucer_code=voucer_code, discount_voucer=discount_voucer, discount_voucer_ongkir=discount_voucer_ongkir, code=code, status_trans=status_trans, shipment_no=shipment_no, shipment_phone=shipment_phone, online_sales_id=online_sales_id, tanggal=tanggal, shipment_service=shipment_service, info=info, total=total, shipment_fee=shipment_fee, products=products, weight_total=weight_total, shipment_name=shipment_name, shipment_address=shipment_address, province_name=province_name, city_name=city_name, postal_code=postal_code, product_name=product_name)  

@bp.route('/customer_list', methods=('GET', 'POST'))
@login_required
def customer_list():
    # meas = [{"MeanCurrent": 0.05933, "Temperature": 15.095, "YawAngle": 0.0, "MeanVoltage": 0.67367, "VoltageDC": 3.18309, "PowerSec": 0.06923, "FurlingAngle": -0.2266828184, "WindSpeed": 1.884, "VapourPressure": 1649.25948, "Humidity": 0.4266, "WindSector": 0, "AirDensity": 1.23051, "BarPressure": 1020.259, "time": "2015-04-22 20:58:28", "RPM": 0.0, "ID": 1357}]
    cursor = db.createCursor()
    cursor.execute("SELECT id, code, init FROM customers")
    dt = cursor.fetchall()
    return jsonify({'data': dt})
