#!/usr/bin/python3.7

import datetime
import sys
import os

import json
import pandas as pd
import numpy as np

pd.options.display.max_columns = None
pd.options.display.float_format = '{:.2f}'.format

prev_date = datetime.datetime.now() - datetime.timedelta(days=1)
prev_filename = str(prev_date.year - 1) + str(prev_date.month).rjust(2, '0') + str(prev_date.day).rjust(2, '0')
present_filename = str(prev_date.year) + str(prev_date.month).rjust(2, '0') + str(prev_date.day).rjust(2, '0')

# previous year
folder = "/data-raw/sales/" + str(prev_date.year - 1)[2:] + str(prev_date.month).rjust(2, "0")
if os.path.isdir(folder):
    if len(os.listdir(folder)) >=1:
        for filename in os.listdir(folder):
            file_date = filename.split('_')
            if file_date[2][:8] == prev_filename:
                names=['KODE_SITE', 'NAMA_SITE', 'KODE_STORE', 'INIT_STORE', 'BDATE', 'MERDIV',
                    'MERDIVDESC', 'MERCAT', 'MERCATDESC', 'MERSCAT', 'MERSCATDESC',
                    'MERCLASS', 'MERCLASSDESC', 'MERSCLASS', 'MERSCLASSDESC', 'TYPE_SKU',
                    'STATUS_SKU', 'STOCK_UNIT', 'SKU', 'SKU_DESC', 'TILLCODE', 'SV', 'TAG',
                    'BRAND', 'PRINCIPLE', 'QTY', 'SALES', 'COGS', 'PPN', 'NETSALES',
                    'PROFIT', 'MARGIN']
                usecols = [
                    'NAMA_SITE', 'KODE_STORE', 'BDATE', 
                    'MERDIV', 'MERDIVDESC', 'MERCAT', 'MERCATDESC', 
                    'SKU', 'SKU_DESC', 'BRAND', 'PRINCIPLE', 'QTY', 'COGS', 'NETSALES', 'PROFIT', 'MARGIN'
                ]
                dtype = {'KODE_STORE' : 'str', 'SKU' : 'str', 'NAMA_SITE' : 'str', 'BDATE' : 'str'}
                
                data = pd.read_csv(folder+'/'+filename, 
                                sep='|', encoding='unicode_escape', 
                                names=names,  usecols=usecols, dtype=dtype)
            else:
                pass
                # print('file : '+prev_filename + ' not found in '+folder)
    else:
        print ('directory : ' + folder + ' has not any file')
else:
    print ('directory : ' + folder + ' not found')

# promo
folder = "/data-raw/promo/" + str(prev_date.year)[2:] + str(prev_date.month).rjust(2, "0")
if os.path.isdir(folder):
    if len(os.listdir(folder)) >=1:
        for filename in os.listdir(folder):
            file_date = filename.split('_')
            if file_date[1][:8] == present_filename:
                dtype = {
                    'kode_store' : 'str', 'sku' : 'str', 'nama_site' : 'str',
                    'rulecode':'str', 'ruletype': 'str', 'tag':'str', 'bdate':'str'
                }
                usecols = [
                    'nama_site', 'kode_store', 'bdate', 
                    'merdiv', 'merdivdesc', 'mercat', 'mercatdesc', 'sku', 'sku_desc',
                    'brand', 'principle', 'rulecode', 'ruletype', 'member',
                    'sku', 'sku_desc', 'brand', 'qty', 'cogs', 'netsales', 'profit', 'tqty', 'tamt', 'tag'
                ]
                
                promo = pd.read_csv(folder+'/'+filename, 
                                sep='|', encoding= 'unicode_escape', 
                                dtype=dtype, usecols=usecols)
            else:
                pass
                # print('file : '+present_filename + ' not found in '+folder)
        
    else:
        print ('directory : ' + folder + ' has not any file')
else:
    print ('directory : ' + folder + ' not found')

# previous year
data.columns = map(str.lower, data.columns)
data = data.drop(data[(data.bdate == 'TRICLE') | (data.bdate == 'SUPREME')].index)
data = data.drop(data[pd.isnull(data.bdate) == True].index)
data = data.drop(data[data.nama_site.apply(str).apply(len) < 3].index)
data = data.drop(data[pd.isnull(data.nama_site) == True].index)
data = data.drop(data[pd.isnull(data.kode_store) == True].index)
data = data.drop(data[data['mercat'].str.isnumeric() == True].index)
data = data.drop(data[pd.to_numeric(data['qty'], errors='coerce').notnull()==False].index)
data = data.drop(data[pd.to_numeric(data['cogs'], errors='coerce').notnull()==False].index)
data = data.drop(data[pd.to_numeric(data['netsales'], errors='coerce').notnull()==False].index)
data = data.drop(data[pd.to_numeric(data['profit'], errors='coerce').notnull()==False].index)
data[data['nama_site'].str.contains('NON AKTIF', na=False)==False]
data['nama_site'] = data['nama_site'].str[-3:]

# convertion
data['qty']=data['qty'].astype('float32')
data['cogs']=data['cogs'].astype('float32')
data['netsales']=data['netsales'].astype('float32')
data['profit']=data['profit'].astype('float32')
data['margin']=data['margin'].astype('float32')

groupby = [
    'nama_site', 'kode_store', 'bdate', 'merdiv', 'merdivdesc','mercat', 'mercatdesc',
    'sku', 'sku_desc', 'brand', 'principle'
]

group_data = data.groupby(groupby).sum().reset_index()

# present
promo = promo.drop(promo[(promo.bdate == 'TRICLE') | (promo.bdate == 'SUPREME')].index)
promo = promo.drop(promo[pd.isnull(promo.bdate) == True].index)
promo = promo.drop(promo[promo.nama_site.apply(str).apply(len) < 3].index)
promo = promo.drop(promo[pd.isnull(promo.nama_site) == True].index)
promo = promo.drop(promo[pd.isnull(promo.kode_store) == True].index)
promo = promo.drop(promo[promo['mercat'].str.isnumeric() == True].index)
promo = promo.drop(promo[pd.to_numeric(promo['qty'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['qty'] <= 0].index)
promo = promo.drop(promo[pd.to_numeric(promo['cogs'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['cogs'] <= 0].index)
promo = promo.drop(promo[pd.to_numeric(promo['netsales'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['netsales'] <= 0].index)
promo = promo.drop(promo[pd.to_numeric(promo['profit'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['profit'] <= 0].index)
promo = promo.drop(promo[pd.to_numeric(promo['tqty'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['tqty'] <= 0].index)
promo = promo.drop(promo[pd.to_numeric(promo['tamt'], errors='coerce').notnull()==False].index)
promo = promo.drop(promo[promo['tamt'] <= 0].index)
promo[promo['nama_site'].str.contains('NON AKTIF', na=False)==False]
promo['nama_site'] = promo['nama_site'].str[-3:]

# calculate netsales per qty
promo['tnetsales'] = (promo['netsales'] / promo['qty']) * promo['tqty']
promo['tcogs'] = (promo['cogs'] / promo['qty']) * promo['tqty']
promo['tprofit'] = (promo['profit'] / promo['qty']) * promo['tqty']

# convertion
promo['qty']=promo['qty'].astype('float32')
promo['cogs']=promo['cogs'].astype('float32')
promo['netsales']=promo['netsales'].astype('float32')
promo['profit']=promo['profit'].astype('float32')
promo['tnetsales']=promo['tnetsales'].astype('float32')
promo['tcogs']=promo['tcogs'].astype('float32')
promo['tprofit']=promo['tprofit'].astype('float32')
promo['tqty']=promo['tqty'].astype('float32')
promo['tamt']=promo['tamt'].astype('float32')

groupby_art = [
    'nama_site', 'kode_store', 'bdate', 'merdiv', 'merdivdesc','mercat', 'mercatdesc',
    'sku', 'sku_desc', 'brand',  'principle', 'rulecode', 'ruletype', 'tag'
]

group_promo = promo.groupby(groupby_art).sum().reset_index()

# save per article
promo_group = group_promo.groupby([
                'bdate', 'kode_store', 'nama_site',  'sku', 
                'tag', 'merdiv', 'merdivdesc', 'mercat', 'mercatdesc', 
                'brand', 'sku_desc', 'principle', 'rulecode', 'ruletype'
            ]).sum().reset_index()

sales_group = group_data.groupby([
                'bdate', 'kode_store', 'nama_site', 'sku', 
                'merdiv', 'merdivdesc', 'mercat', 'mercatdesc', 
                'brand', 'sku_desc', 'principle'
            ]).sum().reset_index()

data_all = pd.merge(sales_group, promo_group, on=['kode_store', 'nama_site', 'sku'], how='inner')
groupby_art = [
    'bdate_y', 'kode_store', 'nama_site', 'sku', 'sku_desc_y', 'merdiv_y', 
    'merdivdesc_y', 'mercat_y', 'mercatdesc_y', 'brand_y', 'principle_y', 'tag',
    'rulecode', 'ruletype'
]

data_art = data_all.groupby(groupby_art).sum().reset_index()

save_col = [
    'bdate_y', 'kode_store', 'nama_site', 'sku', 'sku_desc_y', 'merdiv_y', 'merdivdesc_y', 'mercat_y', 'mercatdesc_y', 'brand_y', 'principle_y', 'tag',
    'qty_x', 'cogs_x', 'netsales_x', 'profit_x', 'qty_y', 'cogs_y', 'netsales_y', 'profit_y', 
    'tqty', 'tnetsales', 'tcogs', 'tprofit', 'rulecode', 'ruletype'
]

data_art = data_art[save_col]
dir_art = '/app/data/data-clean/promo/'+str(prev_date.year)[2:] + str(prev_date.month).rjust(2, '0')
if os.path.isdir(dir_art):
    print (dir_art+' found')
else:
    print (dir_art+' not found, creating directory ...')
    os.system('mkdir '+dir_art+' & chmod -R 777 '+dir_art)

print ('creating : '+dir_art+'/newclean_article_growth_'+present_filename+'.csv')
data_art.to_csv(dir_art+'/newclean_article_growth_'+present_filename+'.csv', sep='|', index=False)

# save per category
data_cat = data_all.groupby(['bdate_y', 'kode_store', 'nama_site', 'mercat_y', 'mercatdesc_y', 'rulecode', 'ruletype']).sum().reset_index()
save_col = [
    'bdate_y', 'kode_store', 'nama_site', 'mercat_y', 'mercatdesc_y', 'rulecode', 'ruletype',
    'qty_x', 'cogs_x', 'netsales_x', 'profit_x', 'qty_y', 'cogs_y', 'netsales_y', 'profit_y', 
    'tqty', 'tnetsales', 'tcogs', 'tprofit'
]

data_cat = data_cat[save_col]
dir_cat = '/app/data/data-clean/promo/'+str(prev_date.year)[2:] + str(prev_date.month).rjust(2, '0')+'/cat'

if os.path.isdir(dir_cat):
    print (dir_cat+' found')
else:
    print (dir_cat+' not found, creating directory ...')
    os.system('mkdir '+dir_cat+' & chmod -R 777 '+dir_cat)

print ('creating : '+dir_cat+'/newclean_cat_growth_' + present_filename + '.csv')
data_cat.to_csv(dir_cat+'/newclean_cat_growth_' + present_filename + '.csv' , sep='|', index=False)

print ('newclean_cat_growth_' + present_filename + '.csv'+', '+'newclean_article_growth_'+present_filename+'.csv'+' created .')
print ('job done\n')