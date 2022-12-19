
from django.core.paginator import Paginator
import time
from django.http import HttpResponse, request, JsonResponse
from django.shortcuts import render , redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from .models import *
from django.db.models import Q
# from .forms import *
from django.db.models import Avg, Max, Min, Sum
import glob,numpy as np,re
# Create your views here.

@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password'] 

        id = auth.authenticate(username=username,password=password)

        if id is not None: #its None not none
            auth.login(request,id) #for logging in process
            
            return render(request,'manage_user.html')
            # return render(request,'products.html',{"username":username,"products":products})
        else:
            messages.info(request,'Invalid credentials try again')
            return redirect('login')
    else:
        return render(request,'login.html')


def manage_product(request):
    return render(request,'manage_product.html')

def manage_user(request):
    return render(request,'manage_user.html')

def manage_config(request):
    # return HttpResponse('fsdfs')
    return render(request,'manage_config.html')

def price_listing(request):
    # return HttpResponse('fsdfs')
    return render(request,'price_listing.html')



def import_to_db(request):
    pass
    start_time = time.time()
    for file in glob.glob(r"files_to_push_to_db\*"):
        print(f'uploading {file}\n')
        df = pd.read_excel(file)

        df = df.replace("'","''",regex = True ).replace(np.nan,'')
        list = df.columns.to_list()
        # print(list)
        # quit()
        for ind,rw in df.iterrows():
            if True:
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

                currency = ''
                if 'price' in list:
                    if '£' in str(rw['price']):
                        currency = '£'
                    elif '€' in str(rw['price']):
                        currency = '€'
                    elif '$' in str(rw['price']):
                        currency = '$'
                    else:
                        currency = 'NA'
                # print(currency)
                # print(rw['price'])
                price = ''
                if 'price' in list:
                    price = rw['price'] 

                live_price = 0
                if 'live_price' in list:
                    try:
                        live_price = int(re.sub('[\$€£ ]','',str(rw['live_price'])) )
                    except:
                        live_price = 0

                special_price = 0
                if 'special_price' in list:
                    try:
                        special_price = int(re.sub('[\$€£ ]','',rw['special_price']) )
                    except:
                        special_price = 0

                discount = 0
                if 'discount' in list:
                    try:
                        discount = int(str(rw['discount']).strip().replace('%','')) 
                    except:
                        discount = 0

                est_retail_price = 0
                if 'est_retail_price' in list:
                    try:
                        est_retail_price = int(re.sub('[\$€£ ]','',str(rw['est_retail_price'])) )
                    except:
                        est_retail_price = 0
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

                if discount != 0:
                    status = 'DISCOUNTED'

                record = ProductData(gender = gender ,brand = brand,category = category,sub_category = sub_category ,description = description,condition = condition,material = material,color = color,currency = currency,price = price,live_price = live_price,special_price = special_price,est_retail_price = est_retail_price,website = website,location = location,datetime_stamp = datetime_stamp,status = status,discount = discount,condition2 = condition2)

                record.save()
               
    end_time = time.time()
    
    return HttpResponse(f"Record import done..Time taken is {end_time-start_time} Seconds..")
