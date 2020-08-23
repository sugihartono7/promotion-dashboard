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
from module.form import ReportSalesForm, ReportProductForm
from werkzeug.exceptions import abort

bp = Blueprint('report', __name__, url_prefix='/back/report')
db = Database()

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[5:6][0]
    return { 'menu' : menu }

@bp.route('/report_sales', methods=('GET', 'POST'))
@login_required
def report_sales():
    form = ReportSalesForm(request.form, csrf_enabled=False)
    return render_template('back/report/sales.html', form=form)

@bp.route('/report_product', methods=('GET', 'POST'))
@login_required
def report_product():
    form = ReportProductForm(request.form, csrf_enabled=False)
    return render_template('back/report/product.html', form=form)

@bp.route('/report_tagihan', methods=('GET', 'POST'))
@login_required
def report_tagihan():
    status = "Menunggu Pembayaran"
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name AS customer_name, b.phone1, b.address FROM view_report_sales a JOIN customers b ON(a.customer_id=b.id) WHERE a.status=%s", (status))
    tagihan = cursor.fetchall()

    return render_template('back/report/tagihan.html', tagihan=tagihan)

@bp.route('/getReportSales', methods=('GET', 'POST'))
@login_required
def getReportSales():
    global sql
    sql = "SELECT * FROM view_report_sales WHERE (created_at >= %s AND created_at <= %s) "
    customer_id = request.form['customer_id']
    sales_type = request.form['sales_type']
    start_date = datetime.datetime.strptime(request.form['start_date'], "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
    end_date = datetime.datetime.strptime(request.form['end_date'], "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
    print(start_date)
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())

    if customer_id != "-1":
        where_customer = " AND customer_id = %s "
    else:
        where_customer = " AND customer_id != %s "

    if sales_type != "-1":
        where_sales_type = " AND sales_type = %s "
    else:
        where_sales_type = " AND sales_type != %s "

    sql = sql + where_customer + where_sales_type
    
    cursor.execute(sql, (start_date, end_date, customer_id, sales_type))
    data = cursor.fetchall()   
    
    return jsonify({'data': data })

@bp.route('/getReportProduct', methods=('GET', 'POST'))
@login_required
def getReportProduct():
    global sql
    sql = "SELECT * FROM view_report_product WHERE (created_at >= %s AND created_at <= %s) "
    product_id = request.form['product_id']
    sales_type = request.form['sales_type']
    start_date = datetime.datetime.strptime(request.form['start_date'], "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
    end_date = datetime.datetime.strptime(request.form['end_date'], "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
    
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())

    if product_id != "-1":
        where_product = " AND product_id = %s "
    else:
        where_product = " AND product_id != %s "

    if sales_type != "-1":
        where_sales_type = " AND sales_type = %s "
    else:
        where_sales_type = " AND sales_type != %s "

    sql = sql + where_product + where_sales_type
    
    cursor.execute(sql, (start_date, end_date, product_id, sales_type))
    data = cursor.fetchall()   
    print(sql)
    return jsonify({'data': data })

@bp.route('/getCustomerList', methods=('GET', 'POST'))
@login_required
def getCustomerList():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.id, a.name, b.name as customer_class_name \
                    FROM customers a JOIN customer_classes b ON(a.customer_class_id=b.id)")
    customers = cursor.fetchall()
    return jsonify({'data': customers })

@bp.route('/getProductList', methods=('GET', 'POST'))
@login_required
def getProductList():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    return jsonify({'data': products })