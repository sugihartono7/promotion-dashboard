import functools
import datetime
import json
import http.client
import sys
from random import randint

sys.path.append("..")
from .auth_front import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from module.form import SearchForm, LoginForm, AccountForm, DropshipperForm
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
# from flask_mail import Mail, Message
# from flask import current_app as app

bp = Blueprint('front', __name__)
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

# @bp.route('/sendmail')
# def sendmail():
#     mail = Mail()
#     mail.init_app(app)
    
#     msg = Message(subject="Hello",
#                     sender=app.config.get("MAIL_USERNAME"),
#                     recipients=["ugie613@gmail.com"])
#     msg.html = "<b>testing</b>"
#     mail.send(msg)
#     return 'success'

@bp.route('/', methods=('GET', 'POST'))
def index():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.* FROM products a JOIN categories b ON(a.category_id=b.id) WHERE a.is_disabled=0 GROUP BY b.name")
    categories = cursor.fetchall()

    cursor.execute("SELECT a.*, c.path \
                    FROM products a LEFT JOIN categories b ON(a.category_id=b.id) \
                    LEFT JOIN product_media c ON(c.product_id=a.id) \
                    WHERE a.is_disabled=0 AND (c.type='image' OR c.type is NULL) \
                    AND (c.sorting=1 OR c.sorting is NULL)")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM splash_screens WHERE is_active=1")
    splash_screen = cursor.fetchone()

    cursor.execute("SELECT * FROM banners WHERE is_active=1")
    banners = cursor.fetchall()

    if session.get('customer_class_id') is not None :
        cursor.execute("SELECT * FROM customer_classes WHERE id=%s", (session['customer_class_id']))
        customer_class = cursor.fetchone()
        percent_discount = customer_class['percent_discount']
    else:
        percent_discount = 0
    
    return render_template('front/index.html', categories=categories, products=products, splash_screen=splash_screen, banners=banners, percent_discount=percent_discount)

@bp.route('/getPopular', methods=('GET', 'POST'))
def getPopular():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.name, b.id FROM populars a JOIN products b ON(a.product_id=b.id) WHERE a.is_active=1 ")
    populars = cursor.fetchall()

    return jsonify({'data': populars })

@bp.route('/countKeranjang', methods=('GET', 'POST'))
def countKeranjang():
    customer_id = getCustomerId()
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT SUM(a.qty) AS total FROM online_sales_details a JOIN online_sales b ON(a.online_sales_id=b.id) WHERE b.customer_id=%s AND b.is_cart=1 GROUP BY a.product_id", (customer_id))
    count = cursor.fetchone()
    if (cursor.rowcount >=1):
        cnt = count['total']
    else:
        cnt = 0

    return str(cnt)

@bp.route('/getTotalPoint', methods=('GET', 'POST'))
# @login_required
def getTotalPoint():
    customer_id = getCustomerId()
    
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.id, a.name AS customer_name, c.name AS customer_class_name, \
                    SUM(b.point) AS total_point \
                    FROM customers a JOIN customer_points b ON(a.id=b.customer_id) \
                    JOIN customer_classes c ON(c.id=a.customer_class_id) \
                    WHERE a.id=%s \
                    GROUP BY a.id, a.name, c.name", (customer_id))
    point = cursor.fetchone()

    if (cursor.rowcount >=1):
        point = point['total_point']
    else:
        point = 0

    return str(point)

@bp.route('/getDropshipperChild', methods=('GET', 'POST'))
@login_required
def getDropshipperChild():
    id = request.args.get('id')
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.ro_province AS province_name, CONCAT(c.ro_type, ' ', c.ro_city_name) AS city_name FROM dropshipper_childs a JOIN provinces b ON(a.province_id=b.ro_province_id) JOIN cities c ON(a.city_id=c.ro_city_id) WHERE a.id=%s", (id))
    dropshipper_child = cursor.fetchall()

    return jsonify({'data': dropshipper_child })

@bp.route('/search', methods=('GET', 'POST'))
def search():
    s = request.args.get('s')
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.path \
                        FROM products a LEFT JOIN product_media b ON(a.id=b.product_id) \
                        WHERE (b.type='image' OR b.type is NULL) \
                        AND (b.sorting=1 OR b.sorting is NULL) \
                        AND a.is_disabled=0 AND a.name LIKE %s", ("%"+s+"%"))
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM customer_classes WHERE id=%s", (session['customer_class_id']))
    customer_class = cursor.fetchone()
    
    return render_template('front/search.html', products=products, s=s, percent_discount=customer_class['percent_discount'])

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name AS category_name FROM products a JOIN categories b ON(a.category_id=b.id) WHERE a.id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/account', methods=('GET', 'POST'))
@login_required
def account():
    email = session['email']

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.* FROM customers a JOIN users b ON(a.id=b.customer_id) WHERE b.email=%s", (email))
    data = cursor.fetchone()

    form = AccountForm(obj=data, csrf_enabled=True)
    if request.method == 'POST' and form.validate_on_submit():
        customer_id = request.form['customer_id'] or 'NULL'
        name = request.form['name'] or 'NULL'
        address = request.form['address'] or 'NULL'
        phone1 = request.form['phone1'] or 'NULL'
        bank_number = request.form['bank_number'] or 'NULL'
        bank_name = request.form['bank_name'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        province_id = request.form['province_id'] or 'NULL'
        city_id = request.form['city_id'] or 'NULL'
        postal_code = request.form['postal_code'] or 'NULL'
        pass1 = request.form['pass1'] or 'NULL'
        pass2 = request.form['pass2'] or 'NULL'
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            if pass1 != 'NULL':
                cursor.execute("UPDATE customers SET \
                                name=%s, address=%s, \
                                phone1=%s, bank_number=%s, province_id=%s, \
                                city_id=%s, postal_code=%s, bank_name=%s, updated_by=%s, password=%s \
                                WHERE id=%s",
                                (name, address, phone1, bank_number, province_id, city_id, postal_code, bank_name, updated_by, generate_password_hash(pass1), customer_id))
            else:
                cursor.execute("UPDATE customers SET \
                                name=%s, address=%s, \
                                phone1=%s, bank_number=%s, province_id=%s, \
                                city_id=%s, postal_code=%s, bank_name=%s, updated_by=%s \
                                WHERE id=%s",
                                (name, address, phone1, bank_number, province_id, city_id, postal_code, bank_name, updated_by, customer_id))    
                
            con.commit()
            flash('Operation success')
            return redirect(url_for('front.account', data=data))
        except:
            con.rollback()
            return redirect(url_for('front.account'))
        finally:
            con.close()

    return render_template('front/account.html', form=form, data=data) 

@bp.route('/dropshipper', methods=('GET', 'POST'))
@login_required
def dropshipper():
    if (session['customer_class_id'] == 2):
        customer_id = getCustomerId()

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        cursor.execute("SELECT a.*, b.ro_province AS province_name, CONCAT(ro_type, ' ', ro_city_name) AS city_name FROM dropshipper_childs a JOIN provinces b ON(a.province_id=b.ro_province_id) JOIN cities c ON(a.city_id=c.ro_city_id) WHERE a.customer_id=%s", (customer_id))
        data = cursor.fetchall()

        return render_template('front/dropshipper.html', data=data) 
    else:
        abort(404, "Page not found") 

@bp.route('/point', methods=('GET', 'POST'))
@login_required
def point():
    customer_id = getCustomerId()
    today = datetime.date.today()

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customer_points WHERE customer_id=%s", (customer_id))
    data = cursor.fetchall()
    
    cursor.execute("SELECT a.id, a.name AS customer_name, c.name AS customer_class_name, \
                    SUM(b.point) AS total_point \
                    FROM customers a JOIN customer_points b ON(a.id=b.customer_id) \
                    JOIN customer_classes c ON(c.id=a.customer_class_id) \
                    WHERE a.id=%s \
                    GROUP BY a.id, a.name, c.name", (customer_id))
    point = cursor.fetchone()

    cursor.execute("SELECT b.*, c.voucer_code, c.start_date, c.end_date, c.id AS customer_voucer_id \
                    FROM promotions a JOIN rewards b ON(a.id=b.promotion_id) \
                    JOIN customer_voucers c ON(c.reward_id=b.id)    \
                    WHERE (a.start_date <=%s AND a.end_date >=%s) \
                        AND (c.start_date <=%s AND c.end_date >=%s) \
                        AND c.is_active=1 AND c.is_redeem=0", (today, today, today, today))
    rewards = cursor.fetchall()
    
    return render_template('front/point.html', data=data, point=point, rewards=rewards) 

@bp.route('/redeem', methods=('GET', 'POST'))
@login_required
def redeem():
    customer_id = getCustomerId()
    customer_voucer_id = request.args.get("customer_voucer_id")
    voucer_code = request.args.get("voucer_code")
    point = request.args.get("point")
    info = "Redeem Voucer "+voucer_code

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    try:
        cursor.execute("UPDATE customer_voucers SET is_redeem=1 WHERE id=%s", (customer_voucer_id))  
        cursor.execute("INSERT INTO  customer_points(info, point, customer_id) \
                        VALUES(%s, %s, %s)", (info, point, customer_id))  
        con.commit()
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        print(message, file=sys.stderr)
        return '0'
    finally:
        con.close()

@bp.route('/<int:id>/dropshipper_detail', methods=('GET', 'POST'))
@login_required
def dropshipper_detail(id): 
    if (session['customer_class_id'] == 2):
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        cursor.execute("SELECT a.*, b.ro_province AS province_name, CONCAT(ro_type, ' ', ro_city_name) AS city_name FROM dropshipper_childs a JOIN provinces b ON(a.province_id=b.ro_province_id) JOIN cities c ON(a.city_id=c.ro_city_id) WHERE a.id=%s", (id))
        data = cursor.fetchone()

        form = DropshipperForm(obj=data, csrf_enabled=True)
        if request.method == 'POST' and form.validate_on_submit():
            name = request.form['name'] or 'NULL'
            address = request.form['address'] or 'NULL'
            phone = request.form['phone'] or 'NULL'
            updated_by = session['user_id'] or 'NULL'
            province_id = request.form['province_id'] or 'NULL'
            city_id = request.form['city_id'] or 'NULL'
            postal_code = request.form['postal_code'] or 'NULL'
            
            con = db.connect()
            cursor = con.cursor(db.getDictCursor())
            try:
                cursor.execute("UPDATE dropshipper_childs SET \
                                name=%s, address=%s, \
                                phone=%s, province_id=%s, \
                                city_id=%s, postal_code=%s, updated_by=%s \
                                WHERE id=%s",
                                (name, address, phone, province_id, city_id, postal_code, updated_by, id))    
                    
                con.commit()
                flash('Operation success')
                return redirect(url_for('front.dropshipper_detail', id=id))
            except:
                con.rollback()
                return redirect(url_for('front.dropshipper_detail'))
            finally:
                con.close()

        return render_template('front/dropshipper_detail.html', form=form, data=data) 
    else:
        abort(404, "Page not found")

@bp.route('/dropshipper/create', methods=('GET', 'POST'))
@login_required
def dropshipper_create():
    if (session['customer_class_id'] == 2):
        customer_id = getCustomerId()

        form = DropshipperForm(request.form, csrf_enabled=True)
        if request.method == 'POST' and form.validate_on_submit():
            name = request.form['name'] or 'NULL'
            address = request.form['address'] or 'NULL'
            phone = request.form['phone'] or 'NULL'
            updated_by = session['user_id'] or 'NULL'
            province_id = request.form['province_id'] or 'NULL'
            city_id = request.form['city_id'] or 'NULL'
            postal_code = request.form['postal_code'] or 'NULL'
            
            con = db.connect()
            cursor = con.cursor(db.getDictCursor())
            try:
                cursor.execute("INSERT INTO dropshipper_childs( \
                                customer_id, name, address, \
                                province_id, city_id, postal_code, \
                                phone, created_by) \
                                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                                (customer_id, name, address, province_id, city_id, postal_code, phone, customer_id))    
                con.commit()
                flash('Operation success')
                return redirect(url_for('front.dropshipper_create', id=id))
            except:
                con.rollback()
                return redirect(url_for('front.dropshipper_create'))
            finally:
                con.close()

        return render_template('front/dropshipper_create.html', form=form) 
    else:
        abort(404, "Page not found")

@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
def dashboard():
    customer_id = getCustomerId()

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.id, a.code, a.created_at, a.status_trans, SUM(b.qty * b.sell_price) AS total \
                    FROM online_sales a JOIN online_sales_details b ON(a.id=b.online_sales_id) \
                    WHERE a.customer_id=%s AND a.is_cart=0 \
                    GROUP BY a.id, a.code, a.created_at, a.status_trans", (customer_id))
    data = cursor.fetchall()

    return render_template('front/dashboard.html', data=data) 

@bp.route('/ulasan', methods=('GET', 'POST'))
@login_required
def ulasan():
    global data, star
    data = ""
    star = ""
    customer_id = getCustomerId()
    
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM online_sales WHERE customer_id=%s AND status_trans='Transaksi Selesai'", (customer_id))
    online_sales = cursor.fetchall()
    for res in online_sales:
        data = data + "<table class='table table-hover smart_toko'> \
                            <thead> \
                                <tr> \
                                    <th class='smart-or-id'><span class='nobr'>Order ID : "+res['code']+"</span></th> \
                                    <th class='smart-or-id' align='right'><span class='nobr'>"+'' if res['created_at'] is None else res['created_at'].strftime('%Y-%m-%d %H:%M:%S')+"</span></th> \
                                </tr> \
                            </thead>"

        cursor.execute("SELECT a.*, b.name AS product_name, b.sku, c.path, d.review, d.rating \
                        FROM online_sales_details a LEFT JOIN products b ON(a.product_id=b.id) \
                        LEFT JOIN product_media c ON(c.product_id=b.id) \
                        LEFT JOIN reviews d ON(a.online_sales_id=d.online_sales_id) \
                        WHERE a.online_sales_id=%s \
                        AND (c.type='image' OR c.type is NULL) \
                        AND (c.sorting=1 OR c.sorting is NULL)", (res['id']))

        online_sales_details = cursor.fetchall()
        for osd in online_sales_details:
            if osd['rating'] is not None :
                for i in range(osd['rating']):
                    star = star + "<i class='fa fa-star' style='color:#FFB900'></i> "

            if osd['review'] is not None :
                data = data + "<tbody><tr class='box'> \
                                        <td class='smart-or-id' style='width:20%'> \
                                            <img src='"+osd['path']+"' style='width:100px;height:100px'> \
                                            <br>"+osd['product_name']+"\
                                        </td> \
                                        <td class='smart-or-date'> "+star+"<br> \
                                            <b>Ulasan</b> : <br><i>"+osd['review']+"</i><br> \
                                        </td> \
                                    </tr></tbody>"
            else:
                data = data + "<tbody><tr class='box'> \
                                        <td class='smart-or-id' style='width:20%'> \
                                            <img src='"+osd['path']+"' style='width:110px;height:110px'> \
                                            <br>"+osd['product_name']+" \
                                        </td> \
                                        <td class='smart-or-date'> \
                                            <select class='star-rating' id='star-rating-"+str(osd['product_id'])+"'> \
                                                <option value='5'></option> \
                                                <option value='4'></option> \
                                                <option value='3'></option> \
                                                <option value='2'></option> \
                                                <option value='1' selected></option> \
                                            </select>\
                                            <textarea name='review[]' id='review-"+str(osd['product_id'])+"' style='width:100%;height:70px'></textarea><br> \
                                            <a href='#' data-sku='"+str(osd['sku'])+"' data-online_sales_code='"+str(res['code'])+"' data-online_sales_id='"+str(osd['online_sales_id'])+"' class='color btn btn-success btn-xs btnKirim' id='btnKirim-"+str(osd['product_id'])+"'>Kirim</a><br> \
                                        </td> \
                                    </tr></tbody>"
        
        data = data + "</table>"

    return render_template('front/ulasan.html', data=data) 

@bp.route('/saveUlasan', methods=('GET', 'POST'))
@login_required
def saveUlasan():
    customer_id = getCustomerId()
    product_id = request.args.get("product_id")
    review = request.args.get("review")
    created_by = getCustomerName()
    rating = request.args.get("rating")
    online_sales_id = request.args.get("online_sales_id")
    online_sales_code = request.args.get("online_sales_code")
    sku = request.args.get("sku")
    info = "Mengulas produk "+str(sku)+" transaksi "+str(online_sales_code)
    point = 50

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    try:
        cursor.execute("INSERT INTO  reviews(product_id, review, created_by, rating, online_sales_id) \
                        VALUES(%s, %s, %s, %s, %s)", (product_id, review, created_by, rating, online_sales_id))  

        cursor.execute("INSERT INTO  customer_points(info, point, customer_id) \
                        VALUES(%s, %s, %s)", (info, point, customer_id))  
        con.commit()
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        print(message, file=sys.stderr)
        return '0'
    finally:
        con.close()

@bp.route('/<int:id>/sales_detail', methods=('GET', 'POST'))
@login_required
def sales_detail(id):
    customer_id = getCustomerId()
    online_sales_id = ""
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
    postal_code = ""
    product_name = ""

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.*, c.name AS product_name, c.sku, \
                    c.weight, a.code, a.created_at AS tanggal, a.status_trans, \
                    a.info, a.shipment_service, a.shipment_name, a.shipment_address, a.postal_code, \
                    a.shipment_fee, d.ro_province AS province_name, \
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
        shipment_fee = products[0]['shipment_fee'] 
        shipment_service = products[0]['shipment_service'] 
        province_name = products[0]['province_name'] 
        city_name = products[0]['city_name'] 
        info = products[0]['info'] 
        shipment_name = products[0]['shipment_name'] 
        shipment_address = products[0]['shipment_address'] 
        postal_code = products[0]['postal_code'] 
        product_name = products[0]['product_name'] 
    
    cursor.execute("SELECT c.id, SUM(a.weight) AS weight_total, SUM(b.sell_price * b.qty) AS total FROM products a JOIN online_sales_details b ON(a.id=b.product_id) JOIN online_sales c ON(c.id=b.online_sales_id) WHERE c.id=%s GROUP BY c.id", (id))
    total = cursor.fetchone()
    weight_total = total['weight_total']
    total = total['total']

    return render_template('front/sales_detail.html', code=code, online_sales_id=online_sales_id, tanggal=tanggal, shipment_service=shipment_service, info=info, total=total, shipment_fee=shipment_fee, products=products, weight_total=weight_total, shipment_name=shipment_name, shipment_address=shipment_address, province_name=province_name, city_name=city_name, postal_code=postal_code, product_name=product_name) 

@bp.route('/keranjang', methods=('GET', 'POST'))
@login_required
def keranjang():
    customer_id = getCustomerId()

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT b.*, c.name AS product_name, \
                    c.sku, c.weight, a.code, d.path \
                    FROM online_sales a JOIN online_sales_details b ON(a.id=b.online_sales_id) \
                    JOIN products c ON(c.id=b.product_id) \
                    JOIN product_media d ON(d.product_id=c.id) \
                    WHERE a.is_cart=1 AND a.customer_id=%s \
                    AND (d.type='image' OR d.type is NULL) \
                    AND (d.sorting=1 OR d.sorting is NULL)", (customer_id))

    products = cursor.fetchall()
    online_sales_id = products[0]['online_sales_id']
    code = products[0]['code']
    
    cursor.execute("SELECT c.id, SUM(a.weight) AS weight_total \
                    FROM products a JOIN online_sales_details b ON(a.id=b.product_id) \
                    JOIN online_sales c ON(c.id=b.online_sales_id) \
                    WHERE c.is_cart=1 GROUP BY c.id")
    total = cursor.fetchone()
    weight_total = total['weight_total']

    cursor.execute("SELECT * FROM voucer_members WHERE customer_id=%s AND is_active=1", (customer_id))
    voucer_members = cursor.fetchall()

    cursor.execute("SELECT a.*, b.name AS reward_name, b.value, b.type \
                    FROM customer_voucers a JOIN rewards b ON(a.reward_id=b.id) \
                    WHERE a.customer_id=%s AND a.is_active=1 AND a.is_redeem=1", (customer_id))
    customer_voucers = cursor.fetchall()

    if request.method == 'POST':
        sales_total = request.form['txt_sales_total'] or 0
        voucer_code = request.form['txt_voucer_code'] 
        discount_voucer = request.form['txt_discount'] or 0
        discount_ongkir = request.form['txt_ongkir'] or 0
        jenis = request.form['txt_jenis']
        type = request.form['txt_type']
        percent_discount = request.form['txt_percent_discount']
        max_amount = request.form['txt_max_amount']

        cursor.execute("SELECT a.*, b.ro_province AS province_name, CONCAT(c.ro_type, ' ', c.ro_city_name) AS city_name FROM customers a JOIN provinces b ON(a.province_id=ro_province_id) JOIN cities c ON(a.city_id=c.ro_city_id) WHERE id=%s", (customer_id))
        customer = cursor.fetchone()

        cursor.execute("SELECT * FROM dropshipper_childs WHERE customer_id=%s", (customer_id))
        dropshipper_childs = cursor.fetchall()

        return render_template('front/checkout.html', code=code, percent_discount=percent_discount, max_amount=max_amount, type = type, jenis=jenis, discount_ongkir=discount_ongkir, weight_total=weight_total, dropshipper_childs=dropshipper_childs, products=products, online_sales_id=online_sales_id, sales_total=sales_total, voucer_code=voucer_code, discount_voucer=discount_voucer, customer=customer) 

    return render_template('front/keranjang.html', products=products, voucer_members=voucer_members, customer_voucers=customer_voucers, online_sales_id=online_sales_id)  

@bp.route('/emptyCart', methods=('GET', 'POST'))
@login_required
def emptyCart():
    online_sales_id = request.args.get('id')
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())

    try:
        cursor.execute("DELETE FROM online_sales_details WHERE online_sales_id=%s", (online_sales_id))
        cursor.execute("DELETE FROM online_sales WHERE id=%s", (online_sales_id))
        con.commit()
        flash('Operation success')
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        print(message, file=sys.stderr)
        return '0'
    finally:
        con.close()

@bp.route('/savePesanan', methods=('GET', 'POST'))
@login_required
def savePesanan():
    customer_id = getCustomerId()
    is_dropshipper = request.form['is_dropshipper']
    online_sales_id = request.form['online_sales_id']
    payment = "transfer"
    shipment_fee = request.form['cost']

    dprovince_id = request.form['dprovince_id']
    dphone = request.form['dphone']
    daddress = request.form['daddress']
    dcity_id = request.form['dcity_id']
    dpostal_code = request.form['dpostal_code']
    dname = request.form['dname']

    province_id = request.form['province_id']
    phone = request.form['phone1']
    address = request.form['address']
    city_id = request.form['city_id']
    postal_code = request.form['postal_code']
    name = request.form['name']

    voucer_code = request.form['txt_voucer_code']
    discount_voucer = request.form['txt_discount_voucer'] or 0
    dropshipper_child_id = request.form['dropshipper_child_id'] or 0
    is_cart = 0
    discount_voucer_ongkir = request.form['pot_ongkir'] or 0
    shipment_service = request.form['service']
    info = request.form['info']
    gross_total = request.form['gross_total']
    code = request.form['code']
    status_trans = "Menunggu Pembayaran"

    nett_total = int(gross_total) - int(discount_voucer) + int(shipment_fee) - int(discount_voucer_ongkir)

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    if request.method == 'POST':
        try:
            if (is_dropshipper == "0"):
                cursor.execute("UPDATE online_sales SET \
                                    payment=%s, shipment_fee=%s, \
                                    province_id=%s, city_id=%s, voucer_code=%s, discount_voucer=%s, \
                                    is_cart=%s, discount_voucer_ongkir=%s, \
                                    shipment_name=%s, shipment_address=%s, shipment_service=%s, \
                                    info=%s, shipment_phone=%s, postal_code=%s, gross_total=%s, \
                                    status_trans=%s \
                                    WHERE id=%s",
                                    (payment, shipment_fee, province_id, city_id, 
                                    voucer_code, discount_voucer, is_cart, 
                                    discount_voucer_ongkir, name, address, shipment_service, info, phone, postal_code, gross_total, status_trans, online_sales_id))    
            else:
                cursor.execute("UPDATE online_sales SET \
                                    payment=%s, shipment_fee=%s, \
                                    province_id=%s, city_id=%s, voucer_code=%s, discount_voucer=%s, \
                                    is_cart=%s, discount_voucer_ongkir=%s, \
                                    shipment_name=%s, shipment_address=%s, shipment_service=%s, \
                                    info=%s, shipment_phone=%s, postal_code=%s, gross_total=%s, \
                                    status_trans=%s \
                                    WHERE id=%s",
                                    (payment, shipment_fee, dprovince_id, dcity_id, 
                                    voucer_code, discount_voucer, is_cart, 
                                    discount_voucer_ongkir, dname, daddress, shipment_service, info, dphone, dpostal_code, gross_total, status_trans, online_sales_id))    
            
            # set active 0 if voucer_members or customer_voucers
            cursor.execute("UPDATE voucer_members SET is_active=0 WHERE customer_id=%s AND voucer_code=%s", (customer_id, voucer_code)) 
            cursor.execute("UPDATE customer_voucers SET is_active=0 WHERE customer_id=%s AND voucer_code=%s", (customer_id, voucer_code)) 
            
            con.commit()
            return redirect(url_for('front.terimakasih', nett_total=nett_total, code=code))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            print(message, file=sys.stderr)
            return redirect(url_for('front.keranjang'))
        finally:
            con.close()

@bp.route('/terimakasih', methods=('GET', 'POST'))
@login_required
def terimakasih():
    nett_total = int(request.args.get('nett_total'))
    code = request.args.get('code')
    return render_template("front/terimakasih.html", nett_total=nett_total, code=code)

@bp.route('/deleteProduct', methods=('GET', 'POST'))
@login_required
def deleteProduct():
    id = request.args.get('id')
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    
    try:
        cursor.execute("DELETE FROM online_sales_details WHERE id=%s", (id))
        con.commit()
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        return '0'
    finally:
        con.close()

@bp.route('/<int:id>/<voucer_code>/<discount>/checkout', methods=('GET', 'POST'))
@login_required
def checkout(id):
    return voucer_code

@bp.route('/<int:id>/produk', methods=('GET', 'POST'))
def produk(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT id FROM products WHERE id=%s AND is_disabled=1", (id))

    if cursor.rowcount >= 1 :
        abort(404, "data not found")
    else:
        global options
        options = ""
        data = get_data(id)
        
        customer_class_id = session.get('customer_class_id')
        if customer_class_id is None:
            percent_discount = 0
        else:
            cursor.execute("SELECT * FROM customer_classes WHERE id=%s", (session['customer_class_id']))
            customer_class = cursor.fetchone()
            percent_discount = customer_class['percent_discount']
        
        cursor.execute("SELECT a.normal_price, a.type_id \
                        FROM products a WHERE a.id=%s", (id))
        product = cursor.fetchone()

        cursor.execute("SELECT a.normal_price, a.type_id, b.path \
                        FROM products a LEFT JOIN product_media b ON(a.id=b.product_id) \
                        WHERE a.id=%s AND (b.type='image' OR b.type is NULL)", (id))
        product_medias = cursor.fetchall()

        cursor.execute("SELECT a.normal_price, a.type_id, b.path \
                        FROM products a LEFT JOIN product_media b ON(a.id=b.product_id) \
                        WHERE a.id=%s AND (b.type='image' OR b.type is NULL) \
                        AND (b.sorting=1 OR b.sorting is NULL)", (id))
        media1 = cursor.fetchone()

        normal_price = product['normal_price'] - (product['normal_price']*(percent_discount / 100))

        cursor.execute("SELECT FORMAT(ROUND(SUM(a.rating)/COUNT(a.rating),0),1) AS total_rating \
                        FROM reviews a \
                        WHERE a.product_id=%s \
                        GROUP BY a.product_id", (id))
        rating = cursor.fetchone()
        
        if cursor.rowcount >= 1:
            total_rating = str(rating['total_rating'])
        else:
            total_rating = "4.0"
        
        star_rating = total_rating.replace(".", "_")

        cursor = con.cursor(db.getDictCursor())
        cursor.execute("SELECT b.*, a.normal_price, a.extra_fee, a.point \
                        FROM products a JOIN product_sizes b ON(a.id=b.product_id) \
                        WHERE a.id=%s", (id))
        sizes = cursor.fetchall()

        for r in sizes:
            price = r['normal_price'] - ((percent_discount / 100) * r['normal_price'])
            if r['size'] == 'XXL':
                p = price + r['extra_fee']
            else:
                p = price
            
            options = options + "<option value='"+r['size']+";"+"{:.0f}".format(p)+";"+"{:.0f}".format(r['point'])+"' >"+r['size']+" - "+"Rp. {:,.0f}".format(p)+"</option>"

        cursor.execute("SELECT b.name, b.id, b.normal_price, c.path \
                        FROM populars a LEFT JOIN products b ON(a.product_id=b.id) \
                        LEFT JOIN product_media c ON(c.product_id=b.id) \
                        WHERE a.is_active=1 AND (c.type='image' OR c.type is NULL) \
                        AND (c.sorting=1 OR c.sorting is NULL) ")
        populars = cursor.fetchall()

        cursor.execute("SELECT * FROM products WHERE is_disabled=0 AND type_id=%s LIMIT 0,3", (product['type_id'] ))
        other_products = cursor.fetchall()
            
        return render_template('front/produk.html', star_rating=star_rating, media1=media1, product_medias=product_medias, data=data, options = options, normal_price=normal_price, populars=populars, percent_discount=percent_discount, other_products=other_products)  

def getCustomerId():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT customer_id FROM users WHERE email=%s", (session['email']))
    r = cursor.fetchone()
    return r['customer_id']

def getCustomerName():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT full_name FROM users WHERE email=%s", (session['email']))
    r = cursor.fetchone()
    return r['full_name']

def getCogs(product_id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT SUM(price * qty) / SUM(qty) AS cogs FROM stock_movements WHERE type='receiving' AND product_id=%s", (product_id))
    r = cursor.fetchone()
    return "{:.0f}".format(r['cogs'])

@bp.route('/addCart', methods=('GET', 'POST'))
@login_required
def addCart():
    product_id = request.args.get("product_id")
    product = request.args.get("product").split(';')

    size = product[0]
    sell_price = product[1]
    point = product[2]
    customer_id = getCustomerId()
    code = generate_code(7)
    created_by = getCustomerId()
    is_cart = 1
    qty = 1
    cogs = getCogs(product_id)
    
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    try:
        # check is cart exists
        cursor.execute("SELECT id FROM online_sales WHERE customer_id=%s AND is_cart=1", (customer_id))
        online_sales = cursor.fetchone()

        if cursor.rowcount >= 1 :
            # check is sales details exists
            cursor.execute("SELECT * FROM online_sales_details WHERE product_id=%s", (product_id))
            if cursor.rowcount < 1 :
                cursor.execute("INSERT INTO \
                                online_sales_details( \
                                    online_sales_id, product_id, qty, sell_price, cogs, point, created_by, size \
                                ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                                (online_sales['id'], product_id, qty, sell_price, cogs, point, created_by, size)
                            )
        else:
            cursor.execute("INSERT INTO \
                            online_sales( \
                                created_by, customer_id, code, is_cart \
                            ) VALUES(%s, %s, %s, %s)", 
                            (created_by, customer_id, code, is_cart)
                        )
            online_sales_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO \
                                online_sales_details( \
                                    online_sales_id, product_id, qty, sell_price, cogs, point, created_by, size \
                                ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                                (online_sales_id, product_id, qty, sell_price, cogs, point, created_by, size)
                            )

        con.commit()
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        return '0'
    finally:
        con.close()

@bp.route('/tentang', methods=('GET', 'POST'))
def tentang():
    return render_template('front/tentang.html')

@bp.route('/panduan', methods=('GET', 'POST'))
def panduan():
    return render_template('front/panduan.html')

@bp.route('/ongkir', methods=('GET', 'POST'))
def ongkir():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM products WHERE is_disabled = 0 ORDER BY created_at DESC LIMIT 0,3")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM customer_classes WHERE id=%s", (session['customer_class_id']))
    customer_class = cursor.fetchone()
    percent_discount = customer_class['percent_discount']

    cursor.execute("SELECT b.name, b.id, b.normal_price FROM populars a JOIN products b ON(a.product_id=b.id) WHERE a.is_active=1 ")
    populars = cursor.fetchall()

    return render_template('front/ongkir.html', products=products, percent_discount=percent_discount, populars=populars)

@bp.route('/konfirmasi', methods=('GET', 'POST'))
def konfirmasi():
    return render_template('front/konfirmasi.html')

@bp.route('/kontak', methods=('GET', 'POST'))
def kontak():
    return render_template('front/kontak.html')
     
@bp.route('/daftar', methods=('GET', 'POST'))
def daftar():
    return render_template('front/daftar.html')

@bp.route('/faq', methods=('GET', 'POST'))
def faq():
    return render_template('front/faq.html')

@bp.route('/tnc', methods=('GET', 'POST'))
def tnc():
    return render_template('front/tnc.html')

@bp.route('/privacy', methods=('GET', 'POST'))
def privacy():
    return render_template('front/privacy.html')

@bp.route('/refund', methods=('GET', 'POST'))
def refund():
    return render_template('front/refund.html')

@bp.route('/blog', methods=('GET', 'POST'))
def blog():
    return render_template('front/blog.html')

@bp.route('/payment', methods=('GET', 'POST'))
def payment():
    return render_template('front/payment.html')

def generate_code(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return str(randint(range_start, range_end))
