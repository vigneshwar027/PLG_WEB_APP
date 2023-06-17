import time
from django.http import HttpResponse, request, JsonResponse
from django.shortcuts import render , redirect
from django.contrib.auth.models import User, auth
# from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from .models import *
from django.db.models import Q
# from .forms import *
from django.db.models import Avg, Max, Min, Sum
import glob,numpy as np,re
from django.contrib.auth.decorators import login_required
from django.db import connection
import csv
from datetime import datetime
import os
from decimal import Decimal
import urllib
import pymongo
from pymongo import MongoClient
import json

database_user = urllib.parse.quote_plus('plgadmin1')
database_pass = urllib.parse.quote_plus('plg@2o2o&*(')
mongo_connection = MongoClient('mongodb://' + database_user + ':' + database_pass +'@34.251.243.79/?authMechanism=SCRAM-SHA-1&authSource=admin&retryWrites=true&w=majority')
db = mongo_connection['plg1']
collection = db['accounts_productdata']
print('Connected to DB')

def test(request):
    return render(request,'price_listing.html')


@login_required(login_url='/')
def manage_config(request):
    if request.user.is_superuser:
    # return HttpResponse('fsdfs')
        return render(request,'configurations.html')
    else:
        return HttpResponse(status=204)


@csrf_exempt
def add_config(request):
    if request.method == 'POST':
        classification = str(request.POST['classification']).strip()
        description = str(request.POST['description']).strip()
        percentage = str(request.POST['percentage']).strip()

        config_record = {"classification":classification,"name":description,"percentage":percentage}

        db.configuration.update_one({"classification":classification,"name":description}, {"$set":config_record},upsert=True)

    return HttpResponse("added")


@csrf_exempt
# @login_required(login_url='/')
def get_config(request):
    if request.method == 'POST':
        configs = db.configuration.find({"classification":{"$in":["brand","season","condition","desirability","model"]}})

        full_count = configs.count()
        filtered_count = full_count
        start = int(request.POST['start'])
        length = int(request.POST['length'])

        
        #Search Filter
        if request.POST['search[value]'] !='':
            search_val = str(request.POST['search[value]']).strip()

            if search_val.__contains__(','):

                search_val = search_val.split(',')
                # time.sleep(100)
                for ind, val in enumerate(search_val) :
                    search_val[ind] = ".*"+val+".*"
                search_val = '|'.join(search_val)
            else:
                search_val = ".*"+search_val+".*"  

            
            configs =  db.configuration.find({"classification":{"$in":["brand","season","condition","desirability","model"]},"$or":[
                         { "classification": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                    { "percentage": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                    { "name": re.compile(f"{search_val}",flags=re.IGNORECASE)}
            ]})
            
            filtered_count = configs.count()

        col_name = ['classification', 'name', 'percentage']

        col_index = int(request.POST['order[0][column]'])
        col_dir = str((request.POST['order[0][dir]'])).strip() 

        # direction
        if col_dir == 'asc':
            col_dir = 1
        else:
            col_dir = -1


        configs = configs.collation({"locale": "en"}).sort(col_name[col_index],col_dir)


        if length == -1:
            configs = configs[start:start+int(configs.count())]
        else:
            configs = configs[start:start+length]
            
        output_data = []
        for config in configs:
            start += 1
            row = [config['classification'], config['name'], config['percentage']]
            output_data.append(row)

        output = {
        "draw": request.POST['draw'],
        "recordsFiltered":filtered_count,
        "recordsTotal":full_count,
        "data": output_data}
        

        return JsonResponse(output)
    

def cl_prc(price):

    try:
        price = round(float(price),2)
    except:
        try:
            price = float(round(price.to_decimal(),2))
        except:
            price = 0
    return price


# @csrf_exempt
# def get_prices(request):
    

#     print('getting price')
#     # time.sleep(100)

#     max_price = "£{:,.2f}".format(cl_prc(col_data['max_price']))
    
#     min_price = "£{:,.2f}".format(cl_prc(col_data['min_price']))
   
#     # avg_price = "£{:,.2f}".format(cl_prc(col_data['avg_price']))

#     agg_sum = "£{:,.2f}".format(cl_prc(col_data['aggregate_sum']))


#     avg_price = "£{:,.2f}".format((cl_prc(col_data['max_price'])+cl_prc(col_data['min_price']))/2)


#     rcnt="{:,}".format(col_data['count'])

#     # print(x)
#     return JsonResponse({"site_data":site_data,"max_price":max_price,"min_price":min_price,"avg_price":avg_price,"agg_sum":agg_sum,"record_count":rcnt})
#     # return render(request,'practice.html')


def logout(request):
    auth.logout(request)
    return redirect('login')


# @csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password'] 
        id = auth.authenticate(username=username, password=password)

        if id is not None: #its None not none
            auth.login(request,id) #for logging in process
            return redirect('manage_product')
        else:
            messages.info(request,'Invalid credentials try again')
            return redirect('login')
    else:
        return render(request,'login.html')


@csrf_exempt
def get_sub_category(request):

    if request.POST['category'] !='':
        category_list = str(request.POST['category']).strip().split('|')
        category_list = [re.compile(f"{x.strip()}",flags=re.IGNORECASE) for x in category_list]

        sub_cats_list = db.filter_pathway.distinct('sub_category',{"category":{"$in":category_list}})
    else:
        sub_cats_list = db.filter_pathway.distinct('sub_category')

    return JsonResponse({"sub_cat_list":sub_cats_list})

@csrf_exempt
def get_category(request):

    if request.POST['gender'] !='':
        gender_list = str(request.POST['gender']).strip().split('|')
        gender_list = [re.compile(f"{x.strip()}",flags=re.IGNORECASE) for x in gender_list]
        category_list = db.filter_pathway.distinct('category',{"gender":{"$in":gender_list}})
    else:
        category_list = db.filter_pathway.distinct('category')

    return JsonResponse({"category_list":category_list})


@login_required(login_url='/')
def manage_product(request):

    brands_list = db.configuration.distinct('name',{"classification":"brand"})
    categories_list = db.configuration.distinct('name',{"classification":"category"})
    sub_cats_list = db.configuration.distinct('name',{"classification":"sub_category"})
    conds_list = db.configuration.distinct('name',{"classification":"condition"})
    # sub_cats_list = []
    
    brands_list = ','.join([str(i) for i in brands_list])

    # brands_list = db.brand.distinct('brand')
    # categories_list = db.category.distinct('category')
    # sub_cats_list = db.sub_category.distinct('sub_category')

    return render(request,'manage_product.html',{'brands':brands_list,'categories':categories_list,'sub_cats':sub_cats_list,'conds':conds_list})



@login_required(login_url='/')
def download_excel(request):

    quer_dict = {}
    if request.session.get('brand','') != '':
        brand_list = str(request.session['brand']).strip().split('|')
        brand_list = [re.escape(val.strip()) for val in brand_list]
        brand_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in brand_list]
        quer_dict['brand'] = {'$in': brand_list}

    if request.session.get('condition2','') !='':
        condition2_list = str(request.session['condition2']).strip().split('|')
        condition2_list = [re.escape(val.strip()) for val in condition2_list]
        condition2_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in condition2_list]

        quer_dict['condition2'] = { '$in': condition2_list }      

    if request.session.get('gender','') !='':
        gender_list = str(request.session['gender']).strip().split('|')
        gender_list = [re.escape(val.strip()) for val in gender_list]
        gender_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in gender_list]

        quer_dict['gender'] = { '$in': gender_list }

    if request.session.get('website','') !='':
        website_list_1 = str(request.session['website']).strip().split('|')
        website_list_1 = [re.escape(val.strip()) for val in website_list_1]
        website_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in website_list_1]

        quer_dict['website'] = { '$in': website_list }
        
    if request.session.get('post_status','') !='':
        post_status_list = str(request.session['post_status']).strip().split('|')
        post_status_list = [re.escape(val.strip()) for val in post_status_list]
        post_status_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in post_status_list]
        quer_dict['status'] = { '$in': post_status_list}
   
    if request.session.get('sub_cat','') !='':
        sub_cat_list = str(request.session['sub_cat']).strip().split('|')
        sub_cat_list = [re.escape(val.strip()) for val in sub_cat_list]
        sub_cat_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in sub_cat_list]
        quer_dict['sub_category'] = { '$in': sub_cat_list}
    
    if request.session.get('category','') !='':
        category_list = str(request.session['category']).strip().split('|')
        category_list = [re.escape(val.strip()) for val in category_list]
        category_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in category_list]
        quer_dict['category'] = {'$in': category_list}


    col_name = request.session.get('col_name','')
    col_index = request.session.get('col_index','')
    col_dir = request.session.get('col_dir','')

    if (col_name != '') and (col_index != '') and (col_dir != ''):
        excel_queryset =  collection.find(quer_dict).sort(col_name[col_index],col_dir)
    else:
        excel_queryset =  collection.find(quer_dict)


    
    df =  pd.DataFrame((excel_queryset))
    df = df.fillna("")
    print('Created dataframe..')
    df_cols = df.columns.tolist()   
    
    unwanted_columns = ['_id','price','id','currency','url']
    price_columns =["live_price","special_price","aggregate_price","est_retail_price"] 			

    def comma_sep(val):
        if val not in ('',0,None):
            try:
                return "£{:,.2f}".format(cl_prc(val))
            except:
                pass

    def add_percent(val):
        if val not in ('',0,None):
            try:
                return str(val)+"%"
            except:
                pass
    
    for col in df_cols: 
        if col in unwanted_columns:
           df = df.drop(col,axis = "columns")   

        if col in price_columns:
            df[col] = df[col].apply(comma_sep)
    
    if 'discount' in df_cols:
        df['discount'] = df['discount'].apply(add_percent)

    cur_date = datetime.now().strftime('%d%m%Y_%H%M%S')
    # filename = f'Downloads/filtered_products_{cur_date}.xlsx'
    filename = f'media/filtered_products_{cur_date}.xlsx'

    df.to_excel(filename,index=False)

    # filename = 'filtered_products.xlsx'
    with open(filename, 'rb') as f:
        response = HttpResponse(f.read(), content_type="application/ms-excel")
        response['Content-Disposition'] = f'attachment; filename=filtered_products_{cur_date}.xlsx'
    
    return response

    
# @csrf_exempt
@login_required(login_url='/')
def manage_user(request):
    if request.user.is_superuser:
        return render(request,'manage_user.html')
    else:
        # pass
        return HttpResponse(status=204)


def price_listing(request):
    # return HttpResponse('fsdfs')
    return render(request,'price_listing.html')

    
@csrf_exempt
def get_offer_price(request):
    if request.method == 'POST':

        website_selected = ''
        if request.POST['website_selected'] !='':
            website_selected = request.POST['website_selected'].split('|')

        brand_selected = ''
        brand_percent=1
        if request.POST['brand_selected'] !='':
            brand_selected = request.POST['brand_selected']
            brand_percent = float(db.configuration.find_one({"classification":"brand","name":re.compile(f"^{brand_selected}",flags=re.IGNORECASE)})['percentage'])/100

        model_selected = ''
        model_percent=1
        if request.POST['model_selected'] !='':
            model_selected = request.POST['model_selected']
            model_percent = float(db.configuration.find_one({"classification":"model","name":re.compile(f"^{model_selected}",flags=re.IGNORECASE)})['percentage'])/100
       
        condition_selected = ''
        condition_percent=1
        if request.POST['condition_selected'] !='':
            condition_selected = request.POST['condition_selected'].strip()
            condition_percent = float(db.configuration.find_one({"classification":"condition","name":re.compile(f"^{condition_selected}",flags=re.IGNORECASE)})['percentage'])/100

        desirability_selected = ''
        desirability_percent=1
        if request.POST['desirability_selected'] !='':
            desirability_selected = request.POST['desirability_selected']
            desirability_percent = float(db.configuration.find_one({"classification":"desirability","name":re.compile(f"^{desirability_selected}",flags=re.IGNORECASE)})['percentage'])/100

        season_selected = ''
        season_percent=1
        if request.POST['season_selected'] !='':
            season_selected = request.POST['season_selected']
            season_percent = float(db.configuration.find_one({"classification":"season","name":season_selected})['percentage'])/100

        html = ''

        websites = ['lampoo','cudoni','realreal','vestiaire']

        final_avg = 0

        for index,website in enumerate(websites):

            price_listing = collection.aggregate([{"$match": {"website":re.compile(f"^{website}",flags=re.IGNORECASE),"brand":re.compile(f"^{brand_selected}",flags=re.IGNORECASE),"condition":re.compile(f"^{condition_selected}",flags=re.IGNORECASE)}},
            {"$group": {"_id": "null", "max_price": {"$max": "$aggregate_price"},"min_price": {"$min": "$aggregate_price"},"avg_price": {"$avg": "$aggregate_price"},}}])

            for i in price_listing:
                max_price = i['max_price']
                min_price = i['min_price']
                avg_price = i['avg_price']
            # print(max_price)
            # print(min_price)
            # print(avg_price)
            try:
              max_price = "£{:,.2f}".format(round(float(max_price),2))
            except:
                try:
                    max_price = "£{:,.2f}".format(float(round(max_price.to_decimal(),2)))
                except:
                    max_price = ''
            
            try:
              min_price = "£{:,.2f}".format(round(float(min_price),2))
            except:
                try:
                    min_price = "£{:,.2f}".format(float(round(min_price.to_decimal(),2)))
                except:
                    min_price = ''


            try:
              avg_price = "£{:,.2f}".format(round(float(avg_price),2))
            except:
                try:
                    avg_price = "£{:,.2f}".format(float(round(avg_price.to_decimal(),2)))
                except:
                    avg_price = ''

            
            try:
                avg_price_in_num =((float(max_price[1:].replace(',',''))+float(min_price[1:].replace(',','')))/2)
                avg_price = "£{:,.2f}".format(avg_price_in_num)
            except:
                avg_price = '-'
                avg_price_in_num = 0

            final_avg+=avg_price_in_num
            # print(avg_price_in_num)
            # print(final_avg)
            # print('\n\n\n')

            # time.sleep(5)
            html+= f'''<tr><td>{website}</td><td>{max_price}</td>
            <td>{min_price}</td>
            <td>{avg_price}</td>
            </tr>''' 

        final_avg = final_avg/float(index+1)

        # print('data')
        # print(final_avg)
        # print(brand_percent)
        # print(model_percent)
        # print(condition_percent)
        # print(desirability_percent)
        # print(season_percent)
        # print('\n\n\n\n')
        final_offer_price = float(final_avg+(final_avg*brand_percent)+(final_avg*model_percent)+(final_avg*condition_percent)+(final_avg*desirability_percent)+(final_avg*season_percent))


        final_avg = "£{:,.2f}".format(round(final_avg,2))



        final_offer_price = "£{:,.2f}".format(final_offer_price)

        html+=f'''<tr>
            <td class="text-right" colspan=3><b>Average Price</b></td>
            <td class="text-center">{final_avg}</td>

            </tr>
            <tr>
            <td class="text-right" colspan=3><b>Rlvd Offer Price</b></td>
            <td class="text-center">{final_offer_price}</td>

       </tr>'''
        # print(html)
        # time.sleep(100)
        return HttpResponse(html)


@csrf_exempt
def get_products(request):

    global quer_dict
    quer_dict = {}

    start = int(request.POST['start'])
    length = int(request.POST['length'])

    brand_list=''
    if request.POST['brand'] !='':
        brand_list = str(request.POST['brand']).strip().split('|')
        brand_list = [re.escape(val.strip()) for val in brand_list]
        brand_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in brand_list]
        quer_dict['brand'] = {'$in': brand_list}

    condition2_list=''
    if request.POST['condition2'] !='':
        condition2_list = str(request.POST['condition2']).strip().split('|')
        condition2_list = [re.escape(val.strip()) for val in condition2_list]
        condition2_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in condition2_list]

        quer_dict['condition2'] = { '$in': condition2_list }
      

    gender_list=''
    if request.POST['gender'] !='':
        gender_list = str(request.POST['gender']).strip().split('|')
        gender_list = [re.escape(val.strip()) for val in gender_list]
        gender_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in gender_list]

        quer_dict['gender'] = { '$in': gender_list }

    # global website_list_1

    # since initially all sites data are needed in side bar
    website_list_1 = ['cudoni','lampoo','realreal','vestiaire']
    # website_list_1 =[]
    if request.POST['website'] !='':
        website_list_1 = str(request.POST['website']).strip().split('|')
        website_list_1 = [re.escape(val.strip()) for val in website_list_1]
        website_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in website_list_1]

        quer_dict['website'] = { '$in': website_list }

    request.session['website_list_1'] = website_list_1

    post_status_list=''
    if request.POST['post_status'] !='':
        post_status_list = str(request.POST['post_status']).strip().split('|')
        post_status_list = [re.escape(val.strip()) for val in post_status_list]
        post_status_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in post_status_list]
        quer_dict['status'] = { '$in': post_status_list}
   
    sub_cat_list=''
    if request.POST['sub_cat'] !='':
        sub_cat_list = str(request.POST['sub_cat']).strip().split('|')
        sub_cat_list = [re.escape(val.strip()) for val in sub_cat_list]
        sub_cat_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in sub_cat_list]
        quer_dict['sub_category'] = { '$in': sub_cat_list}
    
    category_list=''
    if request.POST['category'] !='':
        category_list = str(request.POST['category']).strip().split('|')
        category_list = [re.escape(val.strip()) for val in category_list]
        category_list = [re.compile(f"^{x}$",flags=re.IGNORECASE) for x in category_list]
        quer_dict['category'] = {'$in': category_list}

    


    #Search Filter
    if request.POST['search[value]'] !='':
        search_val = str(request.POST['search[value]']).strip()

        if search_val.__contains__(','):

            search_val = search_val.split(',')
            # time.sleep(100)
            for ind, val in enumerate(search_val) :
                search_val[ind] = ".*"+val+".*"
            search_val = '|'.join(search_val)
        else:
            search_val = ".*"+search_val+".*"  

        
        quer_dict["$or"] =  [
                                { "website": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "gender": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "brand": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "category": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "sub_category": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "description": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "condition2": re.compile(rf"{search_val}",flags=re.IGNORECASE)},
                                { "material": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "color": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "location": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                { "status": re.compile(f"{search_val}",flags=re.IGNORECASE)},
                                ]

    
    
    col_name = ['website', 'gender', 'brand', 'category', 'sub_category', 'description', 'condition2', 'material','color', 'live_price', 'special_price', 'discount','aggregate_price', 'est_retail_price', 'location','sold_date', 'datetime_stamp', 'status']

    col_index = int(request.POST['order[0][column]'])
    col_dir = str((request.POST['order[0][dir]'])).strip() 


    # direction
    if col_dir == 'asc':
        col_dir = 1
    else:
        col_dir = -1

    # storing values for excel queryset
    request.session['brand'] = request.POST['brand']
    request.session['condition2'] = request.POST['condition2']
    request.session['gender'] = request.POST['gender']
    request.session['website'] = request.POST['website']
    request.session['post_status'] = request.POST['post_status']
    request.session['sub_cat'] = request.POST['sub_cat']
    request.session['category'] = request.POST['category']
    request.session['col_name'] = col_name
    request.session['col_index'] = col_index
    request.session['col_dir'] = col_dir

    # print(quer_dict)
    # print('query dict here')

    products = collection.find(quer_dict).sort(col_name[col_index],col_dir)

    # df = pd.DataFrame(products)
    # print('prod len',len(df))
    # excel_queryset =  collection.find(quer_dict).collation({"locale": "en"}).sort(col_name[col_index],col_dir)


    if length != -1:
        products = products[start:start+length]

    output_data = []
    for product in products:

        lprice=str(product['live_price']) if str(product['live_price']) not in ('None','') else ''
        if(lprice!=""):
            lprice1="£{:,.2f}".format(float(lprice))
        else:
            lprice1=""
        sprice=str(product['special_price']) if str(product['special_price']) not in ('None','') else ''
        if(sprice!=""):
            sprice1="£{:,.2f}".format(float(sprice))
        else:
            sprice1=""
        aprice=str(product['aggregate_price']) if str(product['aggregate_price']) not in ('None','') else ''
        if(aprice!=""):
            aprice1="£{:,.2f}".format(float(aprice))
        else:
            aprice1=""
        eprice=str(product['est_retail_price']) if str(product['est_retail_price']) not in ('None','') else ''
        if(eprice!=""):
            eprice1="£{:,.2f}".format(float(eprice))
        else:
            eprice1=""

        start += 1
        row = [product['website'].lower(), product['gender'], product['brand'], product['category'], product['sub_category'],
                product['description'], product['condition2'], product['material'], product['color'], 
                lprice1, sprice1 , str(product['discount'])+'%' if str(product['discount']) not in ('','None') else '', aprice1, eprice1, product['location'], product['sold_date'],product['datetime_stamp'], product['status']]
        output_data.append(row)
  

    count_all = products.count()
	

    output = {
        "draw": request.POST['draw'],
        "recordsFiltered":count_all,
        "recordsTotal":count_all,
        "data": output_data,
    }

    global col_data
    col_data = {}
    col_data['count'] = count_all
    
    return JsonResponse(output)
    
def get_col_data(request):
    global quer_dict

    prices = collection.aggregate([{"$match": quer_dict},
    {"$group": {"_id": "null", \
        "max_price": {"$max": "$aggregate_price"},\
        "min_price": {"$min": "$aggregate_price"},\
        "avg_price": {"$avg": "$aggregate_price"},\
        "aggregate_sum":{"$sum":"$aggregate_price"}}}])

    # global col_data
    
    max_price = '-';min_price='-';avg_price='-';agg_sum='-';rcnt='-'

    for i in prices:
        col_data['max_price'] = (i['max_price'])
        col_data['min_price'] = (i['min_price'])
        col_data['avg_price'] = (i['avg_price'])
        col_data['aggregate_sum'] = (i['aggregate_sum'])

        
        max_price = "£{:,.2f}".format(cl_prc(col_data['max_price']))
        min_price = "£{:,.2f}".format(cl_prc(col_data['min_price']))
        #avg_price = "£{:,.2f}".format(cl_prc(col_data['avg_price']))
        agg_sum = "£{:,.2f}".format(cl_prc(col_data['aggregate_sum']))
        avg_price = "£{:,.2f}".format((cl_prc(col_data['max_price'])+cl_prc(col_data['min_price']))/2)

        rcnt="{:,}".format(col_data['count'])

    return JsonResponse({"max_price":max_price, "min_price":min_price,\
        "avg_price":avg_price, "agg_sum":agg_sum, "record_count":rcnt})
    

def get_site_data(request):

    # global site_data
    # global website_list_1
    website_list_1 = request.session['website_list_1'] 
    site_data={}

    # if len(website_list_1)>0:
    if len(website_list_1)>0:
        for website in website_list_1:
            # print(website)
            site_data[website] = {}
            site_data[website]['site_name'] = website
            # website = str(website).strip()

            quer_dict['website'] = re.compile(f"{website}",flags=re.IGNORECASE)

            site_specific_prices = collection.aggregate([{"$match": quer_dict},{"$group": {"_id": "null","record_count":{"$sum":1}, "max_price": {"$max": "$aggregate_price"},"min_price": {"$min": "$aggregate_price"},"avg_price": {"$avg": "$aggregate_price"},"aggregate_sum":{"$sum":"$aggregate_price"}}}])

            # print('web')

            site_data[(website)]['max_price']='-'
            site_data[(website)]['min_price']='-'
            site_data[(website)]['avg_price']='-'
            site_data[(website)]['aggregate_sum']='-'
            site_data[(website)]['record_count']='-'

            for i in site_specific_prices:
                # print('inhi')
                # print(i)
                site_data[(website)]['max_price'] = "£{:,.2f}".format(cl_prc(i['max_price']))
                site_data[(website)]['min_price'] = "£{:,.2f}".format(cl_prc(i['min_price']))


                site_data[(website)]['avg_price'] = "£{:,.2f}".format((cl_prc(i['max_price'])+cl_prc(i['min_price']))/2)
                
                # site_data[(website)]['avg_price'] = cl_prc(i['avg_price'])
                site_data[(website)]['aggregate_sum'] = "£{:,.2f}".format(cl_prc(i['aggregate_sum']))
                site_data[(website)]['record_count'] =  "{:,}".format(i['record_count'])
    return JsonResponse({"site_data":site_data})

    
def import_to_db(request):
    start_time = time.time()
    for file in glob.glob(r"files_to_push_to_db\*.xlsx"):
        print(f'uploading {file}\n')
        df = pd.read_excel(file)

        df = df.replace("'","''",regex = True ).replace(np.nan,'')
        # df = df.replace("'","''",regex = True ).replace(0.00,None)

        list = df.columns.to_list()
        print('Taken Dataframe')
        # quit()
        for ind,rw in df.iterrows():
            try:
            # if True:
                gender = ''
                if 'gender' in list:
                    gender = rw['gender']

                brand = ''
                if 'brand' in list:
                    brand = rw['brand']

                category = ''
                if 'category' in list:
                    category = rw['category']

                sub_category = ''
                if 'sub_category' in list:
                    sub_category = rw['sub_category']

                description = ''
                if 'description' in list:
                    description = rw['description']

                condition = ''
                if 'condition' in list:
                    condition = rw['condition']
                
                condition2 = ''
                if 'condition2' in list:
                    condition2 = rw['condition2']
                else:    
                    if condition: 
                        try:
                            condition2 = re.search('[\w ]*Good|[\w ]*Excellent|[\w ]*New With Tag',condition,re.IGNORECASE).group()
                        except:
                            pass

                material = ''
                if 'material' in list:
                    material = rw['material']

                color = ''  
                if 'color' in list:
                    color = rw['color']


                currency = '£'

                # currency = ''
                # if 'price' in list:
                #     if '£' in str(rw['price']):
                #         currency = '£'
                #     elif '€' in str(rw['price']):
                #         currency = '€'
                #     elif '$' in str(rw['price']):
                #         currency = '$'
                #     else:
                #         currency = 'NA'

                price = ''
                if 'price' in list:
                    price = rw['price'] 

                live_price = None
                if 'live_price' in list:
                   
                    try:
                        live_price = Decimal(str(rw['live_price']).strip()) 
                    except:
                        live_price = None

                    # try:
                    #     live_price = int(re.sub('[\$€£ ]','',str(rw['live_price'])) )
                    # except:
                    #     live_price = 0

                special_price = None
                if 'special_price' in list:
                    try:
                        special_price = Decimal(str(rw['special_price']).strip()) 
                    except:
                        special_price = None

                    # try:
                    #     special_price = int(re.sub('[\$€£ ]','',rw['special_price']) )
                    # except:
                    #     special_price = 0

                discount = None
                if 'discount' in list:
                    try:
                        discount = (Decimal(str(rw['discount']).strip().replace('%','')) )
                    except:
                        discount = None

                est_retail_price = None
                if 'est_retail_price' in list:
                    try:
                        est_retail_price = Decimal(str(rw['est_retail_price']).strip())
                    except:
                        est_retail_price = None
                    # try:
                    #     est_retail_price = int(re.sub('[\$€£ ]','',str(rw['est_retail_price'])) )
                    # except:
                    #     est_retail_price = 0
                        
                website = ''
                if 'website' in list:
                    website = rw['website']

                location = ''
                if 'location' in list:
                    location = rw['location']

                datetime_stamp = ''
                if 'datetime_stamp' in list:
                    datetime_stamp = rw['datetime_stamp']
               
                status = ''
                if 'status' in list:
                    status = rw['status']

                if (discount != None) and (status.lower() == 'live'):
                    status = 'DISCOUNTED'

                aggregate_price = special_price if special_price not in ['',0,None] else live_price


                record = {
                    "gender":gender,
                    "brand":brand,
                    "category":category,
                    "sub_category":sub_category,
                    "description":description,
                    "condition":condition,
                    "material":material,
                    "color":color,
                    "currency":currency,
                    "price":price,
                    "live_price":live_price,
                    "special_price":special_price,
                    "est_retail_price":est_retail_price,
                    "website":website,
                    "location":location,
                    "datetime_stamp":datetime_stamp,
                    "status":status,
                    "discount":discount,
                    "condition2":condition2,
                    "aggregate_price":aggregate_price

                }
                collection.insert_one()
                
                # record = ProductData(gender = gender ,brand = brand,category = category,sub_category = sub_category ,description = description,condition = condition,material = material,color = color,currency = currency,price = price,live_price = live_price,special_price = special_price,est_retail_price = est_retail_price,website = website,location = location,datetime_stamp = datetime_stamp,status = status,discount = discount,condition2 = condition2,aggregate_price=aggregate_price)

                record.save()
            except Exception as e:
                print(e)
                # quit()
                print(f'Exception arised in file..\n{file}\nIn Row num {ind+1}')
    
    end_time = time.time()
    
    return HttpResponse(f"Record import done..Time taken is {end_time-start_time} Seconds..")





@csrf_exempt
def chk_user_mail_exists(request,id = None):
    if request.method == 'POST':
        email = request.POST['email']
        id = request.POST['id']
        if id:
            user = User.objects.filter(email=email).exclude(id=id)
        else:
            user = User.objects.filter(email=email)
        
        if user:
            return HttpResponse("TRUE")
        else:
            return HttpResponse("FALSE")
        
    return HttpResponse("TRUE")

@csrf_exempt
def add_user(request,id = None):
    if request.method == 'POST':
        id = request.POST['hidden_user_id']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        user_pwd = request.POST['user_pwd']
        user_email = request.POST['user_email']
        user_active = 'false'
        if 'user_active' in request.POST:
            user_active = request.POST['user_active']
        
        # if (user_active) == 'true':
        if (user_active) == 'on':
            user_active = True
        else:
            user_active = False
        
        if id:
            user = User.objects.get(id = id)
            user.first_name = firstname
            user.last_name = lastname
            user.email = user_email
            user.is_active = user_active
            user.username = username
            user.password = user_pwd
        else:
            user = User(first_name = firstname,last_name=lastname,username = username, password = user_pwd, email = user_email, is_active = user_active)

        user.set_password(user_pwd)
        user.save();
        return HttpResponse("saved")

@csrf_exempt
def get_user_list(request):
    users = User.objects.all()
    output = ''
    for user in users:
        output +='<tr>'
        output +='<td class="text-center">'+ str(user.first_name) +'</td>'
        output +='<td class="text-center">'+ str(user.last_name) +'</td>'
        output +='<td class="text-center">'+ str(user.username) +'</td>'
        output +='<td class="text-center">'+ str(user.email) +'</td>'

        if user.is_active:
            checked = 'checked'
            val = '1'
        else:
            checked = ''
            val = '0'
        output +='<td><input type="checkbox" id="check'+str(user.id)+'" class="cbx hidden user_status_btn" '+ checked + ' data-id="'+str(user.id)+'" value="'+val+'"/>\
            <label class="lbl" for="check'+str(user.id)+'" ></label></td>'

        output +='<td class="text-center">'

        output +='<button id="user_button" data-firstname="'+str(user.first_name)+'" data-lastname="'+str(user.last_name)+'" data-id="'+str(user.id)+'" data-user_status="'+str(user.is_active)+'" data-email="'+str(user.email)+'" data-username="'+str(user.username)+'" class="btn btn-warning mr-2 p-1 edit_user" title="Edit" type="button" data-toggle="modal" data-target="#ViewModal">\
			            <i class="mdi mdi-pencil-box-outline"></i>\
                </button>'

        # output +='<button type="button" data-id="'+str(user.id)+'" class="btn btn-danger p-1 delete_user" title="Delete">\
		# 			<i class="mdi mdi-delete-sweep"></i>\
        #         </button>'

        output +='</td>'
        output +='</tr>'
    return HttpResponse(output)


@csrf_exempt
def change_user_status(request):
    if request.method == 'POST':
        id = request.POST['id']
        status = request.POST['status']

        if status == 1 or status == '1':
            user_active = True
        else:
            user_active = False
        #print(user_active)
        user = User.objects.get(id = id)
        if user:
            user.is_active = user_active
            user.save()
    return HttpResponse(True)



@csrf_exempt
def auto_complete_brand(request):
    if request.method == 'POST':
        input = request.POST['input']
        #brand =  db.configuration.distinct('name',{"classification":"brand","name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        brands =  db.configuration.find({"classification":"brand", "name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        brand_list = []
        for brand in brands:
            # print(brand['percentage'])
            brand_list.append({'name': brand['name'], 'percentage':brand['percentage']})
        return JsonResponse({'brand': brand_list})

@csrf_exempt
def auto_complete_model(request):
    if request.method == 'POST':
        input = request.POST['input']
        models =  db.configuration.find({"classification":"model","name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        model_list = []
        for model in models:
            model_list.append({'name': model['name'], 'percentage':model['percentage']})
        return JsonResponse({'model': model_list})

@csrf_exempt
def auto_complete_condition(request):
    if request.method == 'POST':
        input = request.POST['input']
        query =  db.configuration.find({"classification":"condition","name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        query_list = []
        for row in query:
            query_list.append({'name': row['name'], 'percentage':row['percentage']})

        return JsonResponse({'condition': query_list})

@csrf_exempt
def auto_complete_desire(request):
    if request.method == 'POST':
        input = request.POST['input']
        # brands = ProductData.objects.filter(brand__icontains=input).exclude(brand='').order_by('brand').values_list('brand', flat=True).distinct('brand')
        # configs = db.getCollection("configuration").find({"classification":"category","name":re.compile(f"^{input}")})
        
        # category = [config.name for config in configs]
        query =  db.configuration.find({"classification":"desirability","name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        query_list = []
        for row in query:
            query_list.append({'name': row['name'], 'percentage':row['percentage']})
        return JsonResponse({'desire': query_list})


@csrf_exempt
def auto_complete_season(request):
    if request.method == 'POST':
        input = request.POST['input']
        # brands = ProductData.objects.filter(brand__icontains=input).exclude(brand='').order_by('brand').values_list('brand', flat=True).distinct('brand')
        # configs = db.getCollection("configuration").find({"classification":"category","name":re.compile(f"^{input}")})
        
        # category = [config.name for config in configs]
        query =  db.configuration.find({"classification":"season","name":re.compile(f"^{input}",flags=re.IGNORECASE)})
        query_list = []
        for row in query:
            query_list.append({'name': row['name'], 'percentage':row['percentage']})
        return JsonResponse({'season': query_list})



@csrf_exempt
def auto_complete_condition2(request):
    if request.method == 'POST':
        input = request.POST['input']
        condition2 = ProductData.objects.filter(condition2__icontains=input).exclude(condition2='').order_by('condition2').values_list('condition2', flat=True).distinct('condition2')
        condition2 = sorted(list(set(condition2)))
        return JsonResponse({'condition2': condition2})
    
    