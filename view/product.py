import functools
import datetime
import json
import http.client
import os
import sys

sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from module.form import ProductForm
from werkzeug.exceptions import abort
from flask import current_app as app
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

bp = Blueprint('product', __name__, url_prefix='/back/product')
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
    cursor.execute("SELECT a.*, b.name AS category_name, c.name AS type_name \
                     FROM products a JOIN categories b ON(a.category_id=b.id) JOIN types c ON(c.id=a.type_id)")
    products = cursor.fetchall()
    return render_template('back/product/index.html', products=products)

@bp.route('/<int:id>/stock', methods=('GET', 'POST'))
@login_required
def stock(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name, b.sku FROM stock_movements a JOIN products b ON(a.product_id=b.id) WHERE a.product_id=%s", (id))
    stocks = cursor.fetchall()
    return render_template('back/product/stock.html', stocks=stocks)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM types")
    types = cursor.fetchall()
    
    form = ProductForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        sku = request.form['sku'] or 'NULL'
        name = request.form['name'] or 'NULL'
        description = request.form['description'] or 'NULL'
        category_id = request.form['category_id']
        type_id = request.form['type_id']
        normal_price = request.form['normal_price'] or 0
        point = request.form['point'] or 0
        weight = request.form['weight'] or 0
        extra_fee = request.form['extra_fee'] or 0
        created_by = session['user_id'] or 'NULL'
        medias = request.files.getlist("medias[]")
        is_disabled = 'is_disabled' in request.form
        file_url = ""
        sizes = ["S", "M", "L", "XL", "XXL"]
        type = "image"

        if is_disabled == True:
            is_disabled = 1
        else:
            is_disabled = 0

        photos = UploadSet('photos', IMAGES)
        configure_uploads(app, photos)

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO \
                            products( \
                                category_id, type_id, sku, name,\
                                description, normal_price, point, weight, extra_fee, \
                                is_disabled, created_by \
                            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            (category_id, type_id, sku, name, description, normal_price, point, weight, extra_fee, is_disabled, created_by)
                        )
            product_id = cursor.lastrowid

            for size in sizes :
                cursor.execute("INSERT INTO product_sizes(product_id, size) VALUES(%s, %s)", (product_id, size))

            for i, media in enumerate(medias) :
                sorting = str(request.form['sorting_'+str(i+1)])
                if allowed_file(media.filename):
                    filename = photos.save(media)
                    path = photos.url(filename)
                    cursor.execute("INSERT INTO product_media(product_id, path, sorting, type) VALUES(%s, %s, %s, %s)", (product_id, path, sorting, type))
            
            con.commit()
            flash('Operation success')
            return redirect(url_for('product.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('product.create'))
        finally:
            con.close()

    return render_template('back/product/create.html', form=form, categories=categories, types=types)  

@bp.route('/deleteReceiving', methods=('GET', 'POST'))
@login_required
def deleteReceiving():
    id = request.args.get('id')
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    
    try:
        cursor.execute("DELETE FROM stock_movements WHERE id=%s", (id))
        con.commit()
        return '1'
    except cursor.InternalError as e:
        code, message = e.args
        con.rollback()
        return '0'
    finally:
        con.close()

@bp.route('/receiving', methods=('GET', 'POST'))
@login_required
def receiving():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT a.*, b.sku, b.name FROM stock_movements a JOIN products b ON(a.product_id=b.id) WHERE a.type='receiving' ")
    receivings = cursor.fetchall()

    if request.method == 'POST':
        qty = request.form.getlist('qty[]') or 0
        created_by = session['user_id'] or 'NULL'
        type = 'receiving'

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            for i, q in enumerate(qty) :
                if q:
                    product_id = str(request.form['product_id_'+str(i+1)])
                    cogs = str(request.form['cogs_'+str(i+1)])
                    normal_price = str(request.form['normal_price_'+str(i+1)])
                    cursor.execute("INSERT INTO stock_movements \
                                    (product_id, type, price, normal_price, qty, created_by) \
                                    VALUES(%s, %s, %s, %s, %s, %s)", 
                                    (product_id, type, cogs, normal_price, q, created_by))
            con.commit()
            flash('Operation success')
            return redirect(url_for('product.receiving'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('product.receiving'))
        finally:
            con.close()

    return render_template('back/product/receiving.html', products=products, receivings=receivings)    

def get_data(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM products WHERE id = %s", (id))
    data = cursor.fetchone()
    if data is None:
        abort(404, "Data id {0} doesn't exist.".format(id))

    return data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_data(id)
    sizes = []

    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM types")
    types = cursor.fetchall()

    cursor.execute("SELECT * FROM product_sizes WHERE product_id=%s", (id))
    product_sizes = cursor.fetchall()
    for ps in product_sizes:
        sizes.append(ps['size'])

    cursor.execute("SELECT * FROM product_media WHERE product_id=%s", (id))
    product_media = cursor.fetchall()

    form = ProductForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        sku = request.form['sku'] or 'NULL'
        name = request.form['name'] or 'NULL'
        description = request.form['description'] or 'NULL'
        category_id = request.form['category_id']
        type_id = request.form['type_id']
        normal_price = request.form['normal_price'] or 0
        point = request.form['point'] or 0
        weight = request.form['weight'] or 0
        extra_fee = request.form['extra_fee'] or 0
        updated_by = session['user_id'] or 'NULL'
        medias = request.files.getlist("medias[]")
        post_sizes = request.form.getlist("sizes[]")
        is_disabled = 'is_disabled' in request.form
        file_url = ""
        type = "image"

        if is_disabled == True:
            is_disabled = 1
        else:
            is_disabled = 0

        photos = UploadSet('photos', IMAGES)
        configure_uploads(app, photos)

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE \
                            products SET category_id=%s, type_id=%s, sku=%s, \
                            name=%s, description=%s, normal_price=%s, point=%s, \
                            weight=%s, extra_fee=%s, is_disabled=%s, updated_by=%s \
                            WHERE id=%s", 
                            (category_id, type_id, sku, 
                            name, description, normal_price, point, 
                            weight, extra_fee, is_disabled, updated_by, id)
                        )

            cursor.execute("DELETE FROM product_sizes WHERE product_id=%s", (id))
            for ps in post_sizes :
                cursor.execute("INSERT INTO product_sizes(product_id, size) VALUES(%s, %s)", (id, ps))

            for i, media in enumerate(medias) :
                sorting = str(request.form['sorting_'+str(i+1)])
                media_id = str(request.form['id_'+str(i+1)])

                if allowed_file(media.filename):
                    filename = photos.save(media)
                    path = photos.url(filename)
                    if media_id == "" :
                        cursor.execute("INSERT INTO product_media(product_id, path, sorting, type) VALUES(%s, %s, %s, %s)", (id, path, sorting, type))
                    else:
                        cursor.execute("UPDATE product_media SET path=%s WHERE id=%s", (path, media_id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('product.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('product.update', id=id))
        finally:
            con.close()
            
    return render_template('back/product/update.html', form=form, data=data, categories=categories, sizes=sizes, types=types, product_sizes=product_sizes, product_media=product_media)  

@bp.route('/<int:id>/review', methods=('GET', 'POST'))
@login_required
def review(id):
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT a.*, b.name AS product_name FROM reviews a JOIN products b ON(a.product_id=b.id) WHERE b.id=%s", (id))
    reviews = cursor.fetchall()

    product = get_data(id)
    product_name = product['name']
    return render_template('back/product/review.html', reviews=reviews, product_name=product_name)
