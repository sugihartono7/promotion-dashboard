import functools
import datetime
import sys
import os
import pprint
import subprocess
import psycopg2.extras

# sys.path.append("..")
from .auth import login_required

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from module.database import Database
from werkzeug.exceptions import abort
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

# import pyspark 
# from pyspark import SparkContext, SparkConf, SQLContext
# from pyspark import SparkFiles
# from pyspark.sql import SparkSession

import json
import plotly
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import csv
pd.options.display.max_columns = None

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
db = Database()

# sc = pyspark.SparkContext('local[*]')

@bp.context_processor
def inject_today_date():
    return { 'today_date' : datetime.date.today() }

@bp.context_processor
def get_script_root():
    url = request.url
    menu = url.split("/")[4:5][0]
    return { 'menu' : menu }

def toPercent(arr):
    parsed_arr = []
    for i in arr:
        parsed_arr.append(str(i)+'%')
    return parsed_arr

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/getCategoryByDivision', methods=('GET', 'POST'))
@login_required
def getCategoryByDivision():
    division = request.args.get('division')
    if division is None:
        division = '9'

    categories = pd.read_csv('/data-raw/master/mstCat.txt', sep='|', encoding='unicode_escape')
    try:
        categories = categories[categories['cat'].str.slice(0,1) == division]
        return categories.to_json(orient='records')
    except Exception as e:
        print(str(e))

@bp.route('/getDivisionByDirectorate', methods=('GET', 'POST'))
@login_required
def getDivisionByDirectorate():
    directorate = request.args.get('directorate')
    directorates = pd.read_csv('/data-raw/master/directorate_huruf', sep=',', encoding='unicode_escape')
    division_csv = pd.read_csv('/data-raw/master/mstDiv.txt', sep='|', encoding='unicode_escape')
    try:
        divisions = directorates[directorates['dirdesc'] == directorate]
        division_csv = division_csv[division_csv['div'].isin(divisions['directorate_code'])]
        return division_csv.to_json(orient='records')
    except Exception as e:
        print(str(e))
        
@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    typeSalesGrowth = ""
    storeSalesGrowth = ""
    typeSalesShare = ""
    categorySalesGrowth = ""
    categorySalesShare = ""
	
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape')
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
        'dashboard/index.html', 
        typeSalesGrowth=typeSalesGrowth, storeSalesGrowth=storeSalesGrowth, 
        typeSalesShare = typeSalesShare, categorySalesGrowth=categorySalesGrowth,
        categorySalesShare = categorySalesShare,
        stores = stores, directorates = directorates, divisions = divisions,
        _start_date = start_date, _end_date = end_date, _store = store,
        _directorate = directorate, _division = division, _category = category,
        filenames = filenames
    )

@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    global promo, sales
    promo = []
    article = request.args.get("article")
    store = request.args.get("store") or None
    division = request.args.get("division") or None
    directorate = request.args.get("directorate") or None
    category = request.args.get("category") or None
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    filename = request.args.get("filename") or None
    sales_before_df = []
    promo_start_df = []

    # read excel
    excel = pd.read_excel("/app/data/upload/"+filename, sheet_name=0, dtype={'plu': str}, header=0)

    # filter store by yogya/griya only
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape', dtype={'store_code':'str'})
    stores_filter = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA']

    start_date = datetime.datetime.strptime(start_date, '%d-%m-%Y').strftime("%d-%m-%Y")
    end_date = datetime.datetime.strptime(end_date, '%d-%m-%Y').strftime("%d-%m-%Y")
    
    # present date
    daterange = pd.date_range(datetime.datetime.strptime(start_date, '%d-%m-%Y'), datetime.datetime.strptime(end_date, '%d-%m-%Y'))
    year_month_range = daterange.strftime("%y%m").unique()
    file_daterange = daterange.strftime("%Y%m%d")
    
    # last 2 weeks date
    start_date_last = datetime.datetime.strptime(start_date, '%d-%m-%Y') - pd.DateOffset(14)
    end_date_last = datetime.datetime.strptime(start_date, '%d-%m-%Y') - pd.DateOffset(1)
    daterange_last = pd.date_range(start_date_last, end_date_last)
    year_month_last = daterange_last.strftime("%y%m").unique()
    file_daterange_last = daterange_last.strftime("%Y%m%d")

    dtype = {
        'kode_store' : 'str', 'sku' : 'str',
        'qty_x' : 'float32', 'cogs_x' : 'float32', 'netsales_x' : 'float32', 'profit_x' : 'float32', 
        'qty_y' : 'float32', 'cogs_y' : 'float32', 'netsales_y' : 'float32', 'profit_y' : 'float32',
        'tqty': 'float32', 'tnetsales' : 'float32', 'tcogs' : 'float32', 'tprofit' : 'float32',
        'rulecode':'str', 'ruletype':'str'
    }

    # present data
    for year_month in year_month_range:
        folder = "/app/data/data-clean/promo/" + year_month 
        if os.path.isdir(folder):
            if len(os.listdir(folder)) >=1:
                for filename in os.listdir(folder):
                    file_date = filename.split('_')
                    if len(file_date) >=4:
                        if file_date[3][:8] in file_daterange:
                            data = pd.read_csv(folder+'/'+filename, sep='|', encoding= 'unicode_escape', dtype=dtype)
                            data = data[data['sku'].isin(excel['plu'])]
                            data = data[data['kode_store'].isin(stores_filter['store_code'])]
                            promo_start_df.append(data)

                if len(promo_start_df) >= 1:
                    promo_start_dfs = pd.concat(promo_start_df, ignore_index=True)
                else:
                    return 'no data yet'
            else:
                return 'nodata'
        else:
            return 'no directory found'
    
    # last two weeks data
    for year_month in year_month_last:
        folder = "/app/data/data-clean/promo/" + year_month 
        if os.path.isdir(folder):
            if len(os.listdir(folder)) >=1:
                for filename in os.listdir(folder):
                    file_date = filename.split('_')
                    if len(file_date) >=4:
                        if file_date[3][:8] in file_daterange_last:
                            data = pd.read_csv(folder+'/'+filename, sep='|', encoding= 'unicode_escape', dtype=dtype)
                            data = data[data['sku'].isin(excel['plu'])]
                            data = data[data['kode_store'].isin(stores_filter['store_code'])]
                            sales_before_df.append(data)

                if len(sales_before_df) >= 1:
                    sales_before_dfs = pd.concat(sales_before_df, ignore_index=True)
                else:
                    return 'no data yet'
            else:
                return 'no data yet'
        else:
            return 'no directory found'

    promo = promo_start_dfs

    if store != "all":
        promo = promo[promo['kode_store'] == store]
        sales_before_dfs = sales_before_dfs[sales_before_dfs['kode_store'] == store]
    
    promo = promo[promo['sku'] == article]
    sales_before_dfs = sales_before_dfs[sales_before_dfs['sku'] == article]
    
    # data master grouped by day
    during_promo_qty = promo.groupby(['bdate_y']).sum().reset_index()
    during_promo_qty['bdate_y'] = during_promo_qty['bdate_y'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y'))
    during_promo_qty.sort_values('bdate_y', inplace=True, ascending=True)
    during_promo_qty['bdate_y'] = during_promo_qty['bdate_y'].apply(lambda x: x.strftime("%d/%m"))
    during_promo_qty['avg_tcogs'] = np.where(during_promo_qty['tqty'] == 0, 0, during_promo_qty['tcogs'] / during_promo_qty['tqty'])
    during_promo_qty['avg_tnetsales'] = np.where(during_promo_qty['tqty'] == 0, 0, during_promo_qty['tnetsales'] / during_promo_qty['tqty'])
    during_promo_qty['total_margin'] = np.where(during_promo_qty['tnetsales'] == 0, 0, during_promo_qty['tprofit'] / during_promo_qty['tnetsales'])
    during_promo_qty['total_margin'] = during_promo_qty['total_margin'].apply(lambda x: '%.2f' % x)
    during_promo_qty['tqty'] = during_promo_qty['tqty'].apply(lambda x: '{:,.0f}'.format(x))
    during_promo_qty['avg_tcogs'] = during_promo_qty['avg_tcogs'].apply(lambda x: '{:,.0f}'.format(x))
    during_promo_qty['avg_tnetsales'] = during_promo_qty['avg_tnetsales'].apply(lambda x: '{:,.0f}'.format(x))
    
    before_promo_qty = sales_before_dfs.groupby(['bdate_y']).sum().reset_index()
    before_promo_qty['bdate_y'] = before_promo_qty['bdate_y'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y'))
    before_promo_qty.sort_values('bdate_y', inplace=True, ascending=True)
    before_promo_qty['bdate_y'] = before_promo_qty['bdate_y'].apply(lambda x: x.strftime("%d/%m"))
    before_promo_qty['avg_tcogs'] = np.where(before_promo_qty['tqty'] == 0, 0, before_promo_qty['tcogs'] / before_promo_qty['tqty'])
    before_promo_qty['avg_tnetsales'] = np.where(before_promo_qty['tqty'] == 0, 0, before_promo_qty['tnetsales'] / before_promo_qty['tqty'])
    before_promo_qty['total_margin'] = np.where(before_promo_qty['tnetsales'] == 0, 0, before_promo_qty['tprofit'] / before_promo_qty['tnetsales'])
    before_promo_qty['total_margin'] = before_promo_qty['total_margin'].apply(lambda x: '%.2f' % x)
    before_promo_qty['tqty'] = before_promo_qty['tqty'].apply(lambda x: '{:,.0f}'.format(x))
    before_promo_qty['avg_tcogs'] = before_promo_qty['avg_tcogs'].apply(lambda x: '{:,.0f}'.format(x))
    before_promo_qty['avg_tnetsales'] = before_promo_qty['avg_tnetsales'].apply(lambda x: '{:,.0f}'.format(x))

    # plot data
    duringPromoQty = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['tqty'], title='', name='duringPromoQty', plot_type='bar', color='#00a65a', textposition='auto')
    beforePromoQty = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['tqty'], title='Sales Trend per day in Quantity (pcs)', name='beforePromoQty', plot_type='bar', color='#37536d', textposition='auto')
    duringPromoCostPrice = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['avg_tcogs'], title='', name='duringPromoCostPrice', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoCostPrice = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['avg_tcogs'], title='Averages Cost Price Trend per pcs per day (IDR)', name='beforePromoCostPrice', plot_type='scatter', color='#37536d', textposition='top center')
    duringPromoSalesPrice = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['avg_tnetsales'], title='', name='duringPromoSalesPrice', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoSalesPrice = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['avg_tnetsales'], title='Averages Sales Price Trend per pcs per day (IDR)', name='beforePromoSalesPrice', plot_type='scatter', color='#37536d', textposition='top center')
    duringPromoMargin = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['total_margin'], title='', name='duringPromoMargin', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoMargin = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['total_margin'], title='Margin Trend per day (%)', name='beforePromoMargin', plot_type='scatter', color='#37536d', textposition='top center')

    return jsonify(
        _duringPromoQty=duringPromoQty,
        _beforePromoQty=beforePromoQty,
        _duringPromoCostPrice=duringPromoCostPrice,
        _beforePromoCostPrice=beforePromoCostPrice,
        _duringPromoSalesPrice=duringPromoSalesPrice,
        _beforePromoSalesPrice=beforePromoSalesPrice,
        _duringPromoMargin=duringPromoMargin,
        _beforePromoMargin=beforePromoMargin,
    )

@bp.route('/apply', methods=('GET', 'POST'))
@login_required
def apply():
    global promo
    promo = []
    store = request.form['store'] or None
    division = request.form['division'] or None
    directorate = request.form['directorate'] or None
    category = request.form['category'] or None
    promo_date = request.form['promo_date'] or None
    txt_file = request.files['txt_file'] or None
    cb_file = request.form['cb_file'] or None
    promo_start_df = []
    sales_before_df = []
    filenames = []
    excel_name = ""

    # get uploaded file
    for filename in os.listdir("/app/data/upload"):
        filenames.append(filename)

    # process excel
    if txt_file is None:
        excel_name = cb_file
    else:
        if txt_file and allowed_file(txt_file.filename):
            txt_file.save(os.path.join('/app/data/upload', txt_file.filename))
        excel_name = txt_file.filename

    excel = pd.read_excel("/app/data/upload/"+excel_name, sheet_name=0, dtype={'plu': str}, header=0)

    # for dropdown data
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape', dtype={'store_code':'str'})
    stores_filter = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA']
    stores = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA'].sort_values(by=['initial'], ascending=True).to_dict('records')
    directorates = pd.read_csv('/app/data/master/directorate_huruf', sep=',', encoding='unicode_escape')
    directorates_record = directorates.groupby(['dirdesc']).sum().reset_index().to_dict('records')
    division_csv = pd.read_csv('/data-raw/master/mstDiv.txt', sep='|', encoding='unicode_escape')
    divisions = directorates[directorates['dirdesc'] == directorate]
    divisions_record = division_csv[division_csv['div'].isin(divisions['directorate_code'])].to_dict('records')
    categories_csv = pd.read_csv('/data-raw/master/mstCat.txt', sep='|', encoding='unicode_escape')
    categories = categories_csv[categories_csv['cat'].str.slice(0,1) == division]
    categories_record = categories.to_dict('records')
    
    date = promo_date.split(' - ')
    start_date = datetime.datetime.strptime(date[0], '%d-%m-%Y').strftime("%d-%m-%Y")
    end_date = datetime.datetime.strptime(date[1], '%d-%m-%Y').strftime("%d-%m-%Y")
    
    # present date
    daterange = pd.date_range(datetime.datetime.strptime(date[0], '%d-%m-%Y'), datetime.datetime.strptime(date[1], '%d-%m-%Y'))
    year_month_range = daterange.strftime("%y%m").unique()
    file_daterange = daterange.strftime("%Y%m%d")

    # last 2 weeks date
    start_date_last = datetime.datetime.strptime(start_date, '%d-%m-%Y') - pd.DateOffset(14)
    end_date_last = datetime.datetime.strptime(start_date, '%d-%m-%Y') - pd.DateOffset(1)
    daterange_last = pd.date_range(start_date_last, end_date_last)
    year_month_last = daterange_last.strftime("%y%m").unique()
    file_daterange_last = daterange_last.strftime("%Y%m%d")
    
    dtype = {
        'kode_store' : 'str', 'sku' : 'str',
        'qty_x' : 'float32', 'cogs_x' : 'float32', 'netsales_x' : 'float32', 'profit_x' : 'float32', 
        'qty_y' : 'float32', 'cogs_y' : 'float32', 'netsales_y' : 'float32', 'profit_y' : 'float32',
        'tqty': 'float32', 'tnetsales' : 'float32', 'tcogs' : 'float32', 'tprofit' : 'float32',
        'rulecode':'str', 'ruletype':'str'
    }
    
    # present data
    for year_month in year_month_range:
        folder = "/app/data/data-clean/promo/" + year_month
        if os.path.isdir(folder):
            if len(os.listdir(folder)) >=1:
                for filename in os.listdir(folder):
                    file_date = filename.split('_')
                    if len(file_date) >=4:
                        if file_date[3][:8] in file_daterange:
                            data = pd.read_csv(folder+'/'+filename, sep='|', encoding= 'unicode_escape', dtype=dtype, engine='c')
                            data = data[data['sku'].isin(excel['plu'])]
                            data = data[data['kode_store'].isin(stores_filter['store_code'])]
                            promo_start_df.append(data)

                if len(promo_start_df) >= 1:
                    promo_start_dfs = pd.concat(promo_start_df, ignore_index=True)
                else:
                    return 'no data yet'
            else:
                return 'nodata'
        else:
            return 'no directory found'
    
    # last two weeks data
    for year_month in year_month_last:
        folder = "/app/data/data-clean/promo/" + year_month
        if os.path.isdir(folder):
            if len(os.listdir(folder)) >=1:
                for filename in os.listdir(folder):
                    file_date = filename.split('_')
                    if len(file_date) >=4:
                        if file_date[3][:8] in file_daterange_last:
                            data = pd.read_csv(folder+'/'+filename, sep='|', encoding= 'unicode_escape', dtype=dtype, engine='c')
                            data = data[data['sku'].isin(excel['plu'])]
                            data = data[data['kode_store'].isin(stores_filter['store_code'])]
                            sales_before_df.append(data)
                
                if len(sales_before_df) >= 1:
                    sales_before_dfs = pd.concat(sales_before_df, ignore_index=True)
                else:
                    return 'no data yet'
            else:
                return 'no data yet'
        else:
            return 'no directory found'

    # filter data    
    promo = promo_start_dfs
    promo_store = promo

    if store != "all":
        promo = promo[promo['kode_store'] == store]
        sales_before_dfs = sales_before_dfs[sales_before_dfs['kode_store'] == store]

    if category != "" or category is None:
        if category != "all":
            promo = promo[promo['mercat_y'] == category]
            promo_store = promo_store[promo_store['mercat_y'] == category]
            sales_before_dfs = sales_before_dfs[sales_before_dfs['mercat_y'] == category]
        else:
            if directorate != "all" and division == "all":
                # .eg directorate FAS div all
                divisions_by_dir = directorates[directorates['dirdesc'] == directorate]
                promo = promo[promo['mercat_y'].str.slice(0,1).isin(divisions_by_dir['directorate_code'])]
                promo_store = promo_store[promo_store['mercat_y'].str.slice(0,1).isin(divisions_by_dir['directorate_code'])]
                sales_before_dfs = sales_before_dfs[sales_before_dfs['mercat_y'].str.slice(0,1).isin(divisions_by_dir['directorate_code'])]

            elif directorate != "all" and division != "all":
                # .eg directorate FAS div D
                promo = promo[promo['mercat_y'].str.slice(0,1) == division]
                promo_store = promo_store[promo_store['mercat_y'].str.slice(0,1) == division]
                sales_before_dfs = sales_before_dfs[sales_before_dfs['mercat_y'].str.slice(0,1) == division]

    # data master
    if store != "all":
        promo_total = promo.groupby(['kode_store']).sum().reset_index()
        total_netsales = (promo_total['tnetsales'] / 1000000).apply(lambda x: '%.2f' % x)
        total_qty = promo_total['tqty'].apply(lambda x: '{:,.0f}'.format(x))
        sales_growth = np.where(promo_total['netsales_x'] == 0, 0, (((promo_total['tnetsales'] - promo_total['netsales_x']) / promo_total['netsales_x']) * 100 ).apply(lambda x: '%.2f' % x)) 
        qty_growth = np.where(promo_total['qty_x'] == 0, 0, (((promo_total['tqty'] - promo_total['qty_x']) / promo_total['qty_x']) * 100 ).apply(lambda x: '%.2f' % x))
        profit_growth = np.where(promo_total['profit_x'] == 0, 0, (((promo_total['tprofit'] - promo_total['profit_x']) / promo_total['profit_x']) * 100 ).apply(lambda x: '%.2f' % x))
        margin_promo = np.where(promo_total['tnetsales'] == 0, 0, ((promo_total['tprofit'] / promo_total['tnetsales']) * 100 ).apply(lambda x: '%.2f' % x))
        total_netsales = 0 if len(total_netsales)<= 0 else total_netsales[0]
        total_qty = 0 if len(total_qty)<= 0 else total_qty[0]
        sales_growth = 0 if len(sales_growth) <= 0 else sales_growth[0]
        qty_growth = 0 if len(qty_growth) <= 0 else qty_growth[0]
        profit_growth = 0 if len(profit_growth) <= 0 else profit_growth[0]
        margin_promo = 0 if len(margin_promo) <= 0 else margin_promo[0]
    else:
        promo_total = promo.select_dtypes(pd.np.number).sum()
        total_netsales = "{:,.2f}".format(promo_total['tnetsales'] / 1000000)
        total_qty = "{:,.0f}".format(promo_total['tqty'])
        sales_growth = "{:,.2f}".format(np.where(promo_total['netsales_x'] == 0, 0, ((promo_total['tnetsales'] - promo_total['netsales_x']) / promo_total['netsales_x']) * 100 ))
        qty_growth = "{:,.2f}".format(np.where(promo_total['qty_x'] == 0, 0, ((promo_total['tqty'] - promo_total['qty_x']) / promo_total['qty_x']) * 100 ))
        profit_growth = "{:,.2f}".format(np.where(promo_total['profit_x'] == 0, 0, ((promo_total['tprofit'] - promo_total['profit_x']) / promo_total['profit_x']) * 100 ))
        margin_promo = "{:,.2f}".format(np.where(promo_total['tnetsales'] == 0, 0, ((promo_total['tprofit'] / promo_total['tnetsales']) * 100 )))
        total_netsales = 0 if len(total_netsales)<= 0 else total_netsales
        total_qty = 0 if len(total_qty)<= 0 else total_qty
        sales_growth = 0 if len(sales_growth) <= 0 else sales_growth
        qty_growth = 0 if len(qty_growth) <= 0 else qty_growth
        profit_growth = 0 if len(profit_growth) <= 0 else profit_growth
        margin_promo = 0 if len(margin_promo) <= 0 else margin_promo

    # data master grouped by day
    during_promo_qty = promo.groupby(['bdate_y']).sum().reset_index()
    during_promo_qty['bdate_y'] = during_promo_qty['bdate_y'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y'))
    during_promo_qty.sort_values('bdate_y', inplace=True, ascending=True)
    during_promo_qty['bdate_y'] = during_promo_qty['bdate_y'].apply(lambda x: x.strftime("%d/%m"))
    during_promo_qty['avg_tcogs'] = during_promo_qty['tcogs'] / during_promo_qty['tqty']
    during_promo_qty['avg_tnetsales'] = during_promo_qty['tnetsales'] / during_promo_qty['tqty']
    during_promo_qty['total_margin'] = (during_promo_qty['tprofit'] / during_promo_qty['tnetsales']) * 100
    during_promo_qty['total_margin'] = during_promo_qty['total_margin'].apply(lambda x: '%.2f' % x)
    during_promo_qty['tqty'] = during_promo_qty['tqty'].apply(lambda x: '{:,.0f}'.format(x))
    during_promo_qty['avg_tcogs'] = during_promo_qty['avg_tcogs'].apply(lambda x: '{:,.0f}'.format(x))
    during_promo_qty['avg_tnetsales'] = during_promo_qty['avg_tnetsales'].apply(lambda x: '{:,.0f}'.format(x))
    
    before_promo_qty = sales_before_dfs.groupby(['bdate_y']).sum().reset_index()
    before_promo_qty['bdate_y'] = before_promo_qty['bdate_y'].apply(lambda x: datetime.datetime.strptime(x, '%d-%m-%Y'))
    before_promo_qty.sort_values('bdate_y', inplace=True, ascending=True)
    before_promo_qty['bdate_y'] = before_promo_qty['bdate_y'].apply(lambda x: x.strftime("%d/%m"))
    before_promo_qty['avg_tcogs'] = before_promo_qty['tcogs'] / before_promo_qty['tqty']
    before_promo_qty['avg_tnetsales'] = before_promo_qty['tnetsales'] / before_promo_qty['tqty']
    before_promo_qty['total_margin'] = (before_promo_qty['tprofit'] / before_promo_qty['tnetsales']) * 100
    before_promo_qty['total_margin'] = before_promo_qty['total_margin'].apply(lambda x: '%.2f' % x)
    before_promo_qty['tqty'] = before_promo_qty['tqty'].apply(lambda x: '{:,.0f}'.format(x))
    before_promo_qty['avg_tcogs'] = before_promo_qty['avg_tcogs'].apply(lambda x: '{:,.0f}'.format(x))
    before_promo_qty['avg_tnetsales'] = before_promo_qty['avg_tnetsales'].apply(lambda x: '{:,.0f}'.format(x))

    # typeSalesGrowth
    type_sales_growth = promo.groupby(['rulecode', 'ruletype']).sum().reset_index()
    type_sales_growth['growth'] = np.where(type_sales_growth['netsales_x'] == 0, 0,  ((type_sales_growth['tnetsales'] - type_sales_growth['netsales_x']) / type_sales_growth['netsales_x']) * 100)
    type_sales_growth.sort_values(by='growth', ascending=True, inplace=True)
    type_sales_growth['growth'] = type_sales_growth['growth'].apply(lambda x: '%.2f' % x)
    
    # categorySalesGrowth
    category_sales_growth = promo.groupby(['mercat_y', 'mercatdesc_y']).sum().reset_index()
    category_sales_growth['growth'] = np.where(category_sales_growth['netsales_x'] == 0, 0, ((category_sales_growth['tnetsales'] - category_sales_growth['netsales_x']) / category_sales_growth['netsales_x']) * 100) 
    category_sales_growth.sort_values(by='growth', ascending=True, inplace=True)
    category_sales_growth['growth'] = category_sales_growth['growth'].apply(lambda x: '%.2f' % x)
    
    # typeSalesShare
    type_sales_share = promo.groupby(['rulecode', 'ruletype']).sum().reset_index()
    netsales_total = type_sales_share['tnetsales'].sum()
    type_sales_share['share'] = np.where(netsales_total == 0, 0, (type_sales_share['tnetsales'] / netsales_total) * 100)  
    type_sales_share['share'].apply(lambda x: '%.2f' % x)

    # categorySalesShare
    category_sales_share = promo.groupby(['mercat_y', 'mercatdesc_y']).sum().reset_index()
    netsales_total = category_sales_share['tnetsales'].sum()
    category_sales_share['share'] = np.where(netsales_total == 0, 0, (category_sales_share['tnetsales'] / netsales_total) * 100) 
    category_sales_share['share'].apply(lambda x: '%.2f' % x)

    # storeSalesGrowth
    data_store = promo_store.groupby(['kode_store', 'nama_site']).sum().reset_index()
    data_store['growth'] = np.where(data_store['netsales_x'] == 0, 0, ((data_store['tnetsales'] - data_store['netsales_x']) / data_store['netsales_x']) * 100) 
    
    data_store_desc = data_store.sort_values(by='growth', ascending=True)
    data_store_desc['growth'] = data_store_desc['growth'].apply(lambda x: '%.2f' % x)

    data_store = data_store.sort_values(by='growth', ascending=False)
    data_store['growth'] = data_store['growth'].apply(lambda x: '%.2f' % x)

    # plot data
    typeSalesGrowth = barPlot(x=type_sales_growth['growth'][:5], y=type_sales_growth['ruletype'][:5], title='Top Promo Type Sales Growth (%)', name='typeSalesGrowth')
    categorySalesGrowth = barPlot(x=category_sales_growth['growth'][:5], y=category_sales_growth['mercatdesc_y'][:5], title='Top Category Sales Growth (%)', name='categorySalesGrowth')
    typeSalesShare = piePlot(values=type_sales_share['share'][:5], labels=type_sales_share['ruletype'][:5], title='Sales Share of Top Promo Type (%)', name='typeSalesShare')
    categorySalesShare = piePlot(values=category_sales_share['share'][:5], labels=category_sales_share['mercatdesc_y'][:5], title='Sales Share Promo of Top Category (%)', name='categorySalesShare')
    storeSalesGrowth = barPlot(x=data_store['growth'][:5], y=data_store['nama_site'][:5], title='The Best 5 Stores Sales Promo Growth (%)', name='storeSalesGrowth')
    storeSalesGrowthDesc = barPlot(x=data_store_desc['growth'][:5], y=data_store_desc['nama_site'][:5], title='The Worst 5 Stores Sales Promo Growth (%)', name='storeSalesGrowthDesc')
    duringPromoQty = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['tqty'], title='', name='duringPromoQty', plot_type='bar', color='#00a65a', textposition='auto')
    beforePromoQty = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['tqty'], title='Sales Trend per day in Quantity (pcs)', name='beforePromoQty', plot_type='bar', color='#37536d', textposition='auto')
    duringPromoCostPrice = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['avg_tcogs'], title='', name='duringPromoCostPrice', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoCostPrice = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['avg_tcogs'], title='Averages Cost Price Trend per pcs per day (IDR)', name='beforePromoCostPrice', plot_type='scatter', color='#37536d', textposition='top center')
    duringPromoSalesPrice = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['avg_tnetsales'], title='', name='duringPromoSalesPrice', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoSalesPrice = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['avg_tnetsales'], title='Averages Sales Price Trend per pcs per day (IDR)', name='beforePromoSalesPrice', plot_type='scatter', color='#37536d', textposition='top center')
    duringPromoMargin = plotDaily(x=during_promo_qty['bdate_y'], y=during_promo_qty['total_margin'], title='', name='duringPromoMargin', plot_type='scatter', color='#00a65a', textposition='top center')
    beforePromoMargin = plotDaily(x=before_promo_qty['bdate_y'], y=before_promo_qty['total_margin'], title='Margin Trend per day (%)', name='beforePromoMargin', plot_type='scatter', color='#37536d', textposition='top center')

    if float(sales_growth) > 1:
        sales_growth_class = 'bg-green'
    elif float(sales_growth) >= 0:
        sales_growth_class = 'bg-yellow'
    else:
        sales_growth_class = 'bg-red'

    if float(qty_growth) > 1:
        qty_growth_class = 'bg-green'
    elif float(qty_growth) >= 0:
        qty_growth_class = 'bg-yellow'
    else:
        qty_growth_class = 'bg-red'

    if float(profit_growth) > 1:
        profit_growth_class = 'bg-green'
    elif float(profit_growth) >= 0:
        profit_growth_class = 'bg-yellow'
    else:
        profit_growth_class = 'bg-red'
    
    if float(margin_promo) > 1:
        margin_promo_class = 'bg-green'
    elif float(margin_promo) >= 0:
        margin_promo_class = 'bg-yellow'
    else:
        margin_promo_class = 'bg-red'

    return render_template(
        'dashboard/plot.html', 
        typeSalesGrowth=typeSalesGrowth, storeSalesGrowth=storeSalesGrowth, storeSalesGrowthDesc=storeSalesGrowthDesc,
        typeSalesShare = typeSalesShare, categorySalesGrowth=categorySalesGrowth,
        categorySalesShare = categorySalesShare, duringPromoQty=duringPromoQty, beforePromoQty=beforePromoQty,
        duringPromoCostPrice = duringPromoCostPrice, beforePromoCostPrice = beforePromoCostPrice, 
        duringPromoSalesPrice = duringPromoSalesPrice, beforePromoSalesPrice = beforePromoSalesPrice,
        duringPromoMargin = duringPromoMargin, beforePromoMargin = beforePromoMargin,
        stores = stores, divisions = divisions_record, categories = categories_record, directorates = directorates_record,
        _store = store, _division = division, _directorate = directorate, _promo_date = promo_date,
        _category = category, _start_date = start_date, _end_date = end_date,
        total_netsales = total_netsales, 
        total_qty = total_qty,
        sales_growth = sales_growth, qty_growth = qty_growth, 
        profit_growth = profit_growth, margin_promo = margin_promo,
        sales_growth_class = sales_growth_class, qty_growth_class = qty_growth_class,
        profit_growth_class = profit_growth_class, margin_promo_class = margin_promo_class,
        start_date = start_date, end_date = end_date, filenames = filenames,
        _filename = excel_name
    )

@bp.route('/artdetail', methods=('GET', 'POST'))
@login_required
def artdetail():
    global promo
    store = request.args.get("store") or None
    division = request.args.get("division") or None
    directorate = request.args.get("directorate") or None
    category = request.args.get("category") or None
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    filename = request.args.get("filename") or None
    promo = []
    promo_start_df = []
    
    # read excel
    excel = pd.read_excel("/app/data/upload/"+filename, sheet_name=0, dtype={'plu': str}, header=0)
    
    # for dropdown data
    stores_csv = pd.read_csv('/data-raw/master/stores', sep=',', encoding='unicode_escape', dtype={'store_code':'str'})
    stores_filter = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA']
    stores = stores_csv[stores_csv['type_store'] == 'YOGYA/GRIYA'].sort_values(by=['initial'], ascending=True).to_dict('records')
    directorates = pd.read_csv('/app/data/master/directorate_huruf', sep=',', encoding='unicode_escape')
    directorates_record = directorates.groupby(['dirdesc']).sum().reset_index().to_dict('records')
    division_csv = pd.read_csv('/data-raw/master/mstDiv.txt', sep='|', encoding='unicode_escape')
    divisions = directorates[directorates['dirdesc'] == directorate]
    divisions_record = division_csv[division_csv['div'].isin(divisions['directorate_code'])].to_dict('records')
    categories = pd.read_csv('/data-raw/master/mstCat.txt', sep='|', encoding='unicode_escape')
    categories = categories[categories['cat'].str.slice(0,1) == division]
    categories_record = categories.to_dict('records')
    
    start_date = datetime.datetime.strptime(start_date, '%d-%m-%Y').strftime("%d-%m-%Y")
    end_date = datetime.datetime.strptime(end_date, '%d-%m-%Y').strftime("%d-%m-%Y")
    
    # present date
    daterange = pd.date_range(datetime.datetime.strptime(start_date, '%d-%m-%Y'), datetime.datetime.strptime(end_date, '%d-%m-%Y'))
    year_month_range = daterange.strftime("%y%m").unique()
    file_daterange = daterange.strftime("%Y%m%d")
    
    dtype = {
        'kode_store' : 'str', 'sku' : 'str',
        'qty_x' : 'float32', 'cogs_x' : 'float32', 'netsales_x' : 'float32', 'profit_x' : 'float32', 
        'qty_y' : 'float32', 'cogs_y' : 'float32', 'netsales_y' : 'float32', 'profit_y' : 'float32',
        'tqty': 'float32', 'tnetsales' : 'float32', 'tcogs' : 'float32', 'tprofit' : 'float32',
        'rulecode':'str', 'ruletype':'str'
    }

    # data = sc.textFile("clean_art_promo_20200702.csv")
    # spark = SparkSession.builder.getOrCreate()

    # present data
    for year_month in year_month_range:
        folder = "/app/data/data-clean/promo/" + year_month
        if os.path.isdir(folder):
            if len(os.listdir(folder)) >=1:
                for filename in os.listdir(folder):
                    file_date = filename.split('_')
                    if len(file_date) >=4:
                        if file_date[3][:8] in file_daterange:
                            data = pd.read_csv(folder+'/'+filename, sep='|', encoding= 'unicode_escape', dtype=dtype, engine='c')
                            # filter data
                            data = data[data['sku'].isin(excel['plu'])]
                            data = data[data['kode_store'].isin(stores_filter['store_code'])]

                            if store != 'all':
                                data = data[data['kode_store'] == store]

                            if category != "" or category is None:
                                if category != "all":
                                    data = data[data['mercat_y'] == category]
                                else:
                                    if directorate != "all" and division == "all":
                                        # .eg directorate FAS div all
                                        divisions_by_dir = directorates[directorates['dirdesc'] == directorate]
                                        data = data[data['mercat_y'].str.slice(0,1).isin(divisions_by_dir['directorate_code'])]

                                    elif directorate != "all" and division != "all":
                                        # .eg directorate FAS div D
                                        data = data[data['mercat_y'].str.slice(0,1) == division]

                            promo_start_df.append(data)

                            # data = spark.read.csv(folder+'/'+filename, header=True, sep='|').select('*').toPandas()
                            # promo_start_df.append(data)

                            # with open(folder+'/'+filename) as csvfile:
                            #     data = csv.DictReader(csvfile, delimiter='|')
                            #     promo_start_df.append(list(data))

                                # headers = data.fieldnames
                                # for row in data:
                                #     print(row['sku'])

                if len(promo_start_df) >= 1:
                    promo_start_dfs = pd.concat(promo_start_df, ignore_index=True)
                else:
                    return 'no data yet'
            else:
                return 'nodata'
        else:
            return 'no directory found'
    
    
    data = promo_start_dfs

    if promo_start_dfs.empty == False:
        data = data.groupby(['nama_site', 'sku', 'merdiv_y', 'merdivdesc_y', 'mercat_y', 'mercatdesc_y','brand_y', 'sku_desc_y', 'principle_y', 'tag']).sum().reset_index()
    
    data['growth_netsales'] = np.where(data['netsales_x'] == 0, 0,  ((data['tnetsales'] - data['netsales_x']) / data['netsales_x']) * 100)
    data['growth_qty'] = np.where(data['qty_x'] == 0, 0, ((data['tqty'] - data['qty_x']) / data['qty_x']) * 100) 
    data['growth_profit'] = np.where(data['profit_x'] == 0, 0, ((data['tprofit'] - data['profit_x']) / data['profit_x']) * 100)
    data['ty_margin'] = np.where(data['tnetsales'] == 0, 0, (data['tprofit'] / data['tnetsales']) * 100)
    data['ly_margin'] = np.where(data['netsales_x'] == 0, 0, (data['profit_x'] / data['netsales_x']) * 100)
    data['margin_change'] = data['ty_margin'] - data['ly_margin']

    data['growth_netsales'] = data['growth_netsales'].apply(lambda x: '{:,.2f}'.format(x))
    data['growth_qty'] = data['growth_qty'].apply(lambda x: '{:,.2f}'.format(x))
    data['growth_profit'] = data['growth_profit'].apply(lambda x: '{:,.2f}'.format(x))
    data['ty_margin'] = data['ty_margin'].apply(lambda x: '{:,.2f}'.format(x))
    data['ly_margin'] = data['ly_margin'].apply(lambda x: '{:,.2f}'.format(x))
    data['margin_change'] = data['margin_change'].apply(lambda x: '{:,.2f}'.format(x))
    data['tprofit'] = data['tprofit'].apply(lambda x: '{:,.2f}'.format(x))
    data['netsales_x'] = data['netsales_x'].apply(lambda x: '{:,.2f}'.format(x))
    data['profit_x'] = data['profit_x'].apply(lambda x: '{:,.2f}'.format(x))
    data['tnetsales'] = data['tnetsales'].apply(lambda x: '{:,.2f}'.format(x))
    
    data = pd.merge(data, directorates, left_on='merdiv_y', right_on='directorate_code', how='inner')
    data = data.to_dict('records')

    return jsonify({'data': data})

def barPlot(x, y, title, name):
    layout = {
        'title': title, 
        'xaxis': {
            'title' : '',
            'showgrid' : False,
            
        },
        'yaxis': {
            'title' : '', #title x atau y
            'showgrid' : False,
            'categoryorder' : 'total ascending'
        }, 
        # 'margin' : {'autoexpand':True},
        # 'margin' : dict(
        #     l=150,
        #     r=0,
        #     b=0,
        #     t=30,
        #     pad=0
        # ),
        # 'autosize':True,
        'dragmode':False,
        'font':dict(
            family= 'Helvetica',
            size=10
        ), 
        # 'template' : 'plotly',
        'paper_bgcolor':'#e5ecf6'
    }

    config = { 'displayModeBar': False }

    # set conditional color
    clrred = '#dd4b39'
    clrgrn = '#00a65a'
    clrs  = [clrred if n <= 0 else clrgrn for n in pd.to_numeric(x, errors='coerce')]

    data = {
        'type'  : 'bar',
        'x'     : x, 
        'y'     : y,
        'name'  : name,
        'orientation':'h',
        'text': toPercent(x), 
        'textposition' : 'auto',
        'marker': dict(color=clrs)
    }
    
    figure = { 'data': [data], 'layout': layout }
    plot = plotly.offline.plot(
                figure, 
                output_type='div', 
                include_plotlyjs=False,
                config=config,
            )

    return plot

def plotDaily(x, y, title, name, plot_type, color, textposition):
    layout = {
        'title': title, 
        'xaxis': {
            'title':'',
            'showgrid' : True
        },
        'yaxis': {
            'tickformat' : '.0f',
            'showgrid' : True
        }, 
        'dragmode':False,
        'font':dict(
            family= 'Helvetica',
            size=12
        ), 
        # 'template' : 'plotly',
        'paper_bgcolor':'#e5ecf6',
        'margin' : dict(
            l=0,
            r=0,
            b=0,
            t=40,
            pad=0
        )
    }

    config = { 'displayModeBar': False }

    if plot_type != 'bar':
        data = {
            'type'  : plot_type,
            'x'     : x, 
            'y'     : y,
            'name'  : name, 
            'marker_color': color,
            'text' : y,
            'textposition' : textposition,
            'mode':'lines+markers+text',
        }
    else:
        data = {
            'type'  : plot_type,
            'x'     : x, 
            'y'     : y,
            'name'  : name, 
            'marker_color': color,
            'text' : y,
            'textposition' : textposition
        }

    figure = { 'data': [data], 'layout': layout }
    plot = plotly.offline.plot(
                figure, 
                output_type='div', 
                include_plotlyjs=False,
                config=config
                
            )

    return plot

def piePlot(values, labels, title, name):
    layout = {
        'title': title, 
        'xaxis': {
            'title':'',
        },
        'yaxis': {
            'title':'', 
            
        }, 
        'font':dict(
            family= 'Helvetica',
            size=10
        ), 
        'paper_bgcolor':'#e5ecf6'
        # 'margin' : dict(
        #     l=30,
        #     r=30,
        #     b=30,
        #     t=40,
        #     pad=0
        # ),
    }

    config = { 'displayModeBar': False }

    data = {
        'type'  : 'pie',
        'labels'     : labels, 
        'values'     : values,
        'name'  : name,
        'textposition' : 'inside', 
        'textinfo' : 'percent+label',
        # 'hoverinfo':'skip'
    }
    
    figure = { 'data': [data], 'layout': layout, 'layout_showlegend':False}
    plot = plotly.offline.plot(
                figure, 
                output_type='div', 
                include_plotlyjs=False,
                config=config
            )

    return plot
