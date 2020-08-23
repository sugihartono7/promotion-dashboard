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
from module.form import CustomerForm
from werkzeug.exceptions import abort

bp = Blueprint('customer', __name__, url_prefix='/back/customer')
db = Database()

# global vars
sOrder = ""
sLimit = ""
sWhere = ""
rResult = None
output = {}
teks = ""
row = []

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
    cursor.execute("SELECT a.id, a.code, a.name, b.name as customer_class_name, \
                    a.phone1, a.bank_number, a.bank_name \
                    FROM customers a JOIN customer_classes b ON(a.customer_class_id=b.id)")
    customers = cursor.fetchall()
    return render_template('back/customer/index.html', customers=customers)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customer_classes")
    customer_classes = cursor.fetchall()
    
    # ############################################## BEGIN sync provinces #########################################
    # # change the JSON string into a JSON object
    # data = json.loads(ongkir.get_provinces())
    
    # cursor.execute("TRUNCATE TABLE provinces")

    # for i in range(len(data['rajaongkir']['results'])):
    #     cursor.execute("INSERT INTO provinces(ro_province_id, ro_province) VALUES(%s, %s)", (data['rajaongkir']['results'][i]['province_id'], data['rajaongkir']['results'][i]['province']))
    
    # con.commit()
    # # ############################################## END sync provinces #########################################
    
    # # ############################################## END sync cities #########################################
    # # change the JSON string into a JSON object
    # data = json.loads(ongkir.get_cities())
    
    # cursor.execute("TRUNCATE TABLE cities")

    # for i in range(len(data['rajaongkir']['results'])):
    #     cursor.execute("INSERT INTO cities(ro_city_id, ro_province_id, ro_type, ro_city_name, ro_postal_code) VALUES(%s, %s, %s, %s, %s)", (data['rajaongkir']['results'][i]['city_id'], data['rajaongkir']['results'][i]['province_id'], data['rajaongkir']['results'][i]['type'], data['rajaongkir']['results'][i]['city_name'], data['rajaongkir']['results'][i]['postal_code']))
    
    # con.commit()
    # # ############################################## END sync cities #########################################

    form = CustomerForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form['code'] or 'NULL'
        customer_class_id = request.form['customer_class_id']
        name = request.form['name'] or 'NULL'
        address = request.form['address'] or 'NULL'
        phone1 = request.form['phone1'] or 'NULL'
        bank_number = request.form['bank_number'] or 'NULL'
        created_by = session['user_id'] or 'NULL'
        province_id = request.form['province_id'] or 'NULL'
        city_id = request.form['city_id'] or 'NULL'
        postal_code = request.form['postal_code'] or 'NULL'
        bank_name = request.form['bank_name'] or 'NULL'
        point = 500
        info = "Registrasi member baru"

        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("INSERT INTO \
                            customers( \
                                code, customer_class_id, name, address,\
                                phone1, bank_number, created_by, province_id, \
                                city_id, postal_code, bank_name \
                            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            (code, customer_class_id, name, address, phone1, 
                            bank_number, created_by, province_id, city_id, postal_code, bank_name)
                        )
            customer_id = cursor.lastrowid

            cursor.execute("INSERT INTO customer_points(info, point, customer_id) \
                            VALUES(%s, %s, %s)", (info, point, customer_id))  

            con.commit()
            flash('Operation success')
            return redirect(url_for('customer.create'))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            flash(message)
            return redirect(url_for('customer.create'))
        finally:
            con.close()
            
    return render_template('back/customer/create.html', form=form, customer_classes=customer_classes)    

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
    data = get_data(id)
    con = db.connect()
    cursor = con.cursor(db.getDictCursor())
    cursor.execute("SELECT * FROM customer_classes")
    customer_classes = cursor.fetchall()

    form = CustomerForm(obj=data, csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        code = request.form['code'] or 'NULL'
        customer_class_id = request.form['customer_class_id']
        name = request.form['name'] or 'NULL'
        address = request.form['address'] or 'NULL'
        phone1 = request.form['phone1'] or 'NULL'
        bank_number = request.form['bank_number'] or 'NULL'
        province_id = request.form['province_id'] or 'NULL'
        city_id = request.form['city_id'] or 'NULL'
        postal_code = request.form['postal_code'] or 'NULL'
        bank_name = request.form['bank_name'] or 'NULL'
        updated_by = session['user_id'] or 'NULL'
        
        con = db.connect()
        cursor = con.cursor(db.getDictCursor())
        try:
            cursor.execute("UPDATE customers SET \
                            code=%s, customer_class_id=%s, name=%s, address=%s, \
                            phone1=%s, bank_number=%s, province_id=%s, \
                            city_id=%s, postal_code=%s, bank_name=%s, updated_by=%s \
                            WHERE id=%s",
                            (code, customer_class_id, name, address, phone1, bank_number, province_id, city_id, postal_code, bank_name, updated_by, id))
            con.commit()
            flash('Operation success')
            return redirect(url_for('customer.update', id=id))
        except cursor.InternalError as e:
            code, message = e.args
            con.rollback()
            return redirect(url_for('customer.update', id=id))
        finally:
            con.close()
            
    return render_template('back/customer/update.html', form=form, data=data, customer_classes=customer_classes)  

@bp.route('/customer_list', methods=('GET', 'POST'))
@login_required
def customer_list():
    # meas = [{"MeanCurrent": 0.05933, "Temperature": 15.095, "YawAngle": 0.0, "MeanVoltage": 0.67367, "VoltageDC": 3.18309, "PowerSec": 0.06923, "FurlingAngle": -0.2266828184, "WindSpeed": 1.884, "VapourPressure": 1649.25948, "Humidity": 0.4266, "WindSector": 0, "AirDensity": 1.23051, "BarPressure": 1020.259, "time": "2015-04-22 20:58:28", "RPM": 0.0, "ID": 1357}]
    cursor = db.createCursor()
    cursor.execute("SELECT id, code, init FROM customers")
    dt = cursor.fetchall()
    return jsonify({'data': dt})

def customer_list_ajax():
    global sOrder, sLimit, sWhere, rResult, output, teks, row
    
    # meas = [{"MeanCurrent": 0.05933, "Temperature": 15.095, "YawAngle": 0.0, "MeanVoltage": 0.67367, "VoltageDC": 3.18309, "PowerSec": 0.06923, "FurlingAngle": -0.2266828184, "WindSpeed": 1.884, "VapourPressure": 1649.25948, "Humidity": 0.4266, "WindSector": 0, "AirDensity": 1.23051, "BarPressure": 1020.259, "time": "2015-04-22 20:58:28", "RPM": 0.0, "ID": 1357}]
    # return jsonify({'data': meas})

    aColumns = ["id", "code", "init"]
    sIndexColumn = "id"
    sTable = "customers"
    iDisplayStart = request.args.get('iDisplayStart')
    iSortCol_0 = request.args.get('iSortCol_0')

    cursor = db.createCursor()

    # limit
    if iDisplayStart is not None and int(request.args.get('iDisplayLength')) != -1:
        sLimit = "LIMIT " + str(request.args.get('iDisplayStart')) + ", " + str(request.args.get('iDisplayLength'))

    # order by
    if iSortCol_0 is not None:
        sOrder = "ORDER BY  "
        for i in range (int(request.args.get('iSortingCols'))):
            if request.args.get('bSortable_' + str(int(request.args.get('iSortCol_'+str(i))))) == True:
                tmpColumns = int(request.args.get('iSortCol_'+str(i)))
                sOrder = sOrder + aColumns[tmpColumns] + " " + request.args.get('sSortDir_'+str(i)) + ", "
        
        sOrder = sOrder[-2:]
        if sOrder == "ORDER BY":
            sOrder = ""

    # where
    if request.args.get('sSearch') != "":
        sWhere = "WHERE ("
        for i in range(len(aColumns)):
            sWhere = sWhere + aColumns[i] + " LIKE '%" + request.args.get('sSearch') + "%' OR "

        sWhere = sWhere[:-3]
        sWhere = sWhere + ")"

    # row data
    qry = "SELECT SQL_CALC_FOUND_ROWS " + ", ".join(aColumns).replace(" , ", " ") + " FROM  %s %s %s %s" % (sTable, sWhere, sOrder, sLimit)
    rResult = cursor.execute(qry)
    rResult = cursor.fetchall()
    # return qry

    # count rows
    sQuery = "SELECT FOUND_ROWS() as found_rows"
    cursor.execute(sQuery)
    iFilteredTotal = cursor.fetchone()['found_rows']
    sQuery = "SELECT COUNT(" + sIndexColumn + ") AS cnt FROM %s" % (sTable)
    cursor.execute(sQuery)
    iTotal = cursor.fetchone()['cnt']

    # output
    output = {
        "sEcho" : int(request.args.get('sEcho')),
        "iTotalRecords" : iTotal,
        "iTotalDisplayRecords" : iFilteredTotal,
        "aaData" : []
    }

    # ["Gecko","Mozilla 1.1", "Win 95+ / OSX.1+"], ["Gecko","Mozilla 1.2","Win 95+ / OSX.1+"]

    for aRow in rResult:
        # teks = teks + aRow['code']
        for i in range(len(aColumns)):
            if aColumns[i] == "version":
                row.append("-" if aRow[aColumns[i]] == 0 else aRow[aColumns[i]])
            elif aColumns[i] != ' ':
                row.append(aRow[aColumns[i]])

        # row.append([aRow['id'], aRow['code'], aRow['init']])
    
        output['aaData'] = [row]
    
    return json.dumps(output)

