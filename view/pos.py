import functools
import datetime
import json
import http.client
import sys
from random import randint

sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from werkzeug.exceptions import abort

bp = Blueprint('pos', __name__, url_prefix='/back/pos')
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[4:5][0]
    return { 'menu' : menu }

@bp.route('/getCustomerList', methods=('GET', 'POST'))
def getCustomerList():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.percent_discount FROM customers a JOIN customer_classes b ON(a.customer_class_id=b.id) ")
    customers = cursor.fetchall()

    return jsonify({'data': customers })


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT (SUM(b.qty*b.sell_price) - a.discount + a.shipment_fee) AS total, \
                    a.id, a.code, a.status, a.created_at, c.name AS customer_name \
                    FROM sales a JOIN sales_details b ON(a.id=b.sales_id) \
                    JOIN customers c ON(c.id=a.customer_id) \
                    GROUP BY a.id, a.code, a.status,a.created_at, c.name ")
    pos = cursor.fetchall()
    return render_template('back/pos/index.html', pos=pos)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())

    cursor.execute("SELECT * FROM customer_classes")
    customer_classes = cursor.fetchall()

    cursor.execute("SELECT a.*, SUM(b.price * b.qty) / SUM(b.qty) AS cogs, c.path \
                    FROM products a join stock_movements b ON(a.id=b.product_id) \
                    LEFT JOIN product_media c ON(c.product_id=a.id) \
                    WHERE b.type='receiving' \
                    AND (c.type='image' OR c.type IS NULL) \
                    AND (c.sorting=1 OR c.sorting IS NULL) \
                    GROUP BY b.product_id")
    products = cursor.fetchall()
    
    if request.method == "POST":
        customer_id = request.form['customer_id'].split(";")
        info = request.form['info']
        shipment_fee = request.form['shipment_fee'] or 0
        is_percent = 'is_percent' in request.form
        discount = request.form['discount'] or 0
        payment = request.form['payment']
        code = generate_code(7)
        status = "processed"
        created_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        qty = request.form.getlist('qty[]') or 0
        address = request.form['address']
        city_id = request.form['city_id'] or 0
        province_id = request.form['province_id'] or 0
        postal_code = request.form['postal_code']
        phone1 = request.form['phone1']
        name = request.form['name']
        created_by = session['user_id'] or 'NULL'
        type = "sales-in-store"
        
        if is_percent == True:
            is_percent = 1
        else:
            is_percent = 0
        
        try:
            cursor.execute("INSERT INTO sales \
                            (code, customer_id, payment, shipment_fee, \
                            status, info, created_at, created_by, discount, is_percent, \
                            shipment_name, shipment_address, shipment_phone, shipment_postal_code, \
                            shipment_province, shipment_city)    \
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (code, customer_id[0], payment, shipment_fee, status, 
                            info, created_at, created_by, discount, is_percent,
                            name, address, phone1, postal_code, province_id, city_id)
                        )
            sales_id = cursor.lastrowid

            for i, q in enumerate(qty) :
                if q:
                    product_id = str(request.form['txt_product_id_'+str(i)])
                    sell_price = str(request.form['sell_price_'+str(i)])
                    cogs = str(request.form['cogs_'+str(i)])
                    point = str(request.form['point_'+str(i)])
                    size = str(request.form['txt_size_'+str(i)])
                    qty_movements = int(q) * -1

                cursor.execute("INSERT INTO sales_details \
                                (sales_id, product_id, qty, sell_price, \
                                cogs, discount, point, created_at, created_by, size) \
                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                (sales_id, product_id, q, sell_price, cogs, discount, point, created_at, created_by, size)
                            )
                
                cursor.execute("INSERT INTO stock_movements \
                                (product_id, type, price, qty, created_by) \
                                VALUES(%s, %s, %s, %s, %s)",
                                (product_id, type, sell_price, qty_movements, created_by)
                            )

            con.commit()
            return '1'
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return message
        finally:
            con.close()

        return render_template('back/pos/create.html', products=products, customer_classes=customer_classes)
        
    return render_template('back/pos/create.html', products=products, customer_classes=customer_classes)

@bp.route('/saveCustomer', methods=('GET', 'POST'))
@login_required
def saveCustomer():
    if request.method == 'POST':
        new_customer_class = request.form['new_customer_class']
        new_customer_name = request.form['new_customer_name']
        new_customer_phone = request.form['new_customer_phone']
        new_customer_address = request.form['new_customer_address']
        created_by = session['user_id'] or 'NULL'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO customers(customer_class_id, name, phone1, address, created_by) \
                            VALUES(%s, %s, %s, %s, %s)",
                            (new_customer_class, new_customer_name, new_customer_phone, new_customer_address, created_by))
            con.commit()
            flash('Operation success')
            return redirect(url_for('pos.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('pos.create'))
        finally:
            con.close()

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    sales_id = id
    code = ""
    tanggal = ""
    status = ""
    shipment_fee = 0
    shipment_service = ""
    province_name = ""
    city_name = ""
    info = ""
    shipment_name = ""
    shipment_address = ""
    shipment_phone = ""
    shipment_postal_code = ""
    product_name = ""
    shipment_no = ""
    discount = 0
    is_percent = 0

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.*, c.name AS product_name, c.sku, \
                    c.weight, a.code, a.created_at AS tanggal, a.status, a.shipment_no, \
                    a.info, a.shipment_service, a.shipment_name, \
                    a.shipment_address, a.shipment_postal_code, a.shipment_phone, \
                    a.shipment_fee, d.ro_province AS province_name, \
                    CONCAT(e.ro_type, ' ', e.ro_city_name) AS city_name \
                    FROM sales a JOIN sales_details b ON(a.id=b.sales_id) \
                    JOIN products c ON(c.id=b.product_id) \
                    LEFT JOIN provinces d ON(d.ro_province_id=a.shipment_province)    \
                    LEFT JOIN cities e ON(e.ro_city_id=a.shipment_city)    \
                    WHERE a.id=%s", (id))
    products = cursor.fetchall()

    if (cursor.rowcount >= 1):
        sales_id = products[0]['sales_id'] 
        code = products[0]['code'] 
        tanggal = products[0]['tanggal'] 
        status = products[0]['status'] 
        shipment_no = products[0]['shipment_no'] 
        shipment_fee = products[0]['shipment_fee'] 
        shipment_service = products[0]['shipment_service'] 
        province_name = products[0]['province_name'] 
        city_name = products[0]['city_name'] 
        info = products[0]['info'] 
        shipment_name = products[0]['shipment_name'] 
        shipment_address = products[0]['shipment_address'] 
        shipment_postal_code = products[0]['shipment_postal_code'] 
        product_name = products[0]['product_name'] 
        shipment_phone = products[0]['shipment_phone'] 
    
    cursor.execute("SELECT c.id, SUM(a.weight) AS weight_total, \
                    SUM(b.sell_price * b.qty) AS total, c.is_percent, c.discount \
                    FROM products a JOIN sales_details b ON(a.id=b.product_id) \
                    JOIN sales c ON(c.id=b.sales_id) \
                    WHERE c.id=%s \
                    GROUP BY c.id", (id))

    getTotal = cursor.fetchone()
    weight_total = getTotal['weight_total']
    total = getTotal['total']
    
    is_percent = getTotal['is_percent']
    
    if is_percent == 1:
        discount = (getTotal['discount']/100) * getTotal['total']
        print(discount)
    else:
        discount = getTotal['discount']

    if request.method == 'POST':
        status = request.form['status']
        shipment_no = request.form['shipment_no']
        updated_at = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        updated_by = session['user_id'] or 'NULL'
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE sales SET \
                            status=%s, updated_at=%s, shipment_no=%s \
                            WHERE id=%s",
                            (status, updated_at, shipment_no, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('pos.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('pos.update', id=id))
        finally:
            con.close()
            
    return render_template('back/pos/update.html', code=code, status=status, shipment_no=shipment_no, shipment_phone=shipment_phone, sales_id=sales_id, tanggal=tanggal, shipment_service=shipment_service, info=info, total=total, shipment_fee=shipment_fee, products=products, weight_total=weight_total, shipment_name=shipment_name, shipment_address=shipment_address, province_name=province_name, city_name=city_name, shipment_postal_code=shipment_postal_code, product_name=product_name, discount=discount, is_percent=is_percent)  

def generate_code(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return str(randint(range_start, range_end))
