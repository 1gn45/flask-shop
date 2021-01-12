import gspread
import json
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from bs4 import BeautifulSoup
from cssutils import parseStyle
import csv
from shopfunctions import getproductinfo, productinputinfo, getpricelistfromuserdict, deliveryprices
import time
from flask import render_template
from flask_weasyprint import HTML, render_pdf
import os

seller={'name':os.environ.get("seller_name"), 'sellercode':os.environ.get("seler_idcode"), 'selleremail':os.environ.get("seller_mail"), 'indveikloskodas':os.environ.get('seller_businessidcode'),'sellerphone':os.environ.get('seller_phone'), 'bankacc':os.environ.get('seller_bankacc')}
shopname=os.environ.get('shopname')


serverfolder= os.environ.get("directories_eshopdir")
credentialsfile=serverfolder+'/creds.json'
ShopGoogleFolder=os.environ.get("directories_googleeshopdir")
orderlistfile=os.environ.get("googledisc_orders/orderlist")
paymentsfile=os.environ.get("googledisc_payments/payments")
SwedbankPaymentsID=os.environ.get("googledisc_payments/SwedbankPaymentsTXT")
unpaidordersjsonID=os.environ.get('googledisc_orders/unpaidordersJson')

tmpfolderdest='shop/tmp/'
SvgFolderID=os.environ.get('googlediscfolderid_orders/SVGS')
SvgProcessedFolderID=os.environ.get('googlediscfolderid_orders/SVGS/processed')
SvgFinishedFolderID=os.environ.get('googlediscfolderid_orders/SVGS/finished')

SvgInkscapePreparedFolderID=os.environ.get('googlediscfolderid_orders/SVGS/processed/inkscape')
paymenterrors=os.environ.get('googledisc_orders/errors/paymenterrors')


##########eshop/order/orders data txt files - FOLDERIU ID
EshopOrderdatatxtfilesFinishedID=os.environ.get('googlediscfolderid_orders/orderdatatxtfiles/finishedorders')
EshopOrderdatatxtfilesID=os.environ.get('googlediscfolderid_orders/orderdatatxtfiles')
##############

def prgetorderlist():
    orderlist_files={2019:orderlistfile}

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    client=gspread.authorize(credentials)
    date=datetime.datetime.now()
    sheet=client.open_by_key(orderlist_files[2019])
    sheet=sheet.worksheet('orders')
    data=sheet.get_all_records()
    rowvalues=sheet.row_values(1)
    return (data)


def getuserdicts(orderexelrows):
    userdictids=[]
    for a in orderexelrows:
        userdictids.append(a[23])

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    userdicts=[]
    for a in userdictids:
        file = drive.CreateFile({'id': a})
        file.GetContentFile('shop/tmp/orderdict.txt')
        with open('shop/tmp/orderdict.txt', 'r') as u:
            userdicts.append(u.readlines())
    #userdicts=json.loads(userdicts[0][0][0])
    return str(userdicts[0][0])



def makesvg(orderexelrows):

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)

    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')

    for a in orderexelrows:#####################dalinam i atskirus uzsakymus
        orderdictlink=a[23]
        orderid=a[0]
        file = drive.CreateFile({'id': orderdictlink})
        file.GetContentFile('shop/tmp/orderdict.txt')
        with open('shop/tmp/orderdict.txt', 'r') as u:
            userdict=u.readlines()
        userdict=json.loads(userdict[0])
        productcounter=1
        orderedproductsdata={}
        for singleproduct in userdict:  ##############dalinam i atskirus produktus uzsakyme(veliau reiks dalinti i atskirus sio produkto vienetus)
            prinfo=getproductinfo(singleproduct['productid'])
            if prinfo['type']=='personalised':
                productinfoinputs=productinputinfo(singleproduct['productid'])

            with open('shop/templates/svgs/'+ singleproduct['productid'] +'mf'+'.svg','r') as soup:
                soup = BeautifulSoup(soup.read(), features ='xml')
            svgdatalist={'orderid':orderid, 'product id':singleproduct['productid'], 'svg':soup, 'material':prinfo['material'], 'thickness':prinfo['thickness'], 'width':prinfo['width'], 'height':prinfo['height'], 'price':prinfo['price'], 'weight':prinfo['weight']}
            for everysinglesvggenerator in singleproduct['productlist']:
                svgname='OrderId='+str(orderid)+', product='+str(productcounter)+', material='+prinfo['material']+prinfo['thickness']+', price='+prinfo['price']

                orderedproductsdata[svgname+'.svg']={'product id':singleproduct['productid'], 'svgname':svgname+'.svg',
                                    'material':prinfo['material'], 'thickness':prinfo['thickness'], 'width':prinfo['width'],
                                    'height':prinfo['height'], 'price':prinfo['price'], 'weight':prinfo['weight'], 'inputdata':everysinglesvggenerator, 'status':'SVG only generated','Who is manufacturing':'Noone yet'}

                soup.find(id= 'orderid').string=str(orderid)
                productcounter+=1
                if prinfo['type']=='personalised':
                    for feature in productinfoinputs:######Loopinam per svg pakeiciamus laukelius ir ikeliam userio inputus
                        if feature[2]=='text':
                            soup.find(id= feature[4]).string=everysinglesvggenerator[feature[1]]
                        if feature[2]=='font-size':
                            style=parseStyle(soup.find(id= feature[4])['style'])
                            style['font-size']=everysinglesvggenerator[feature[1]]
                            soup.find(id= feature[4])['style'] = style.cssText

                        if feature[2]=='img':
                            if everysinglesvggenerator[feature[1]] in singleproduct['imglist']:
                                soup.find(id= feature[4])["xlink:href"]= singleproduct['imglist'][everysinglesvggenerator[feature[1]]]
                            else:
                                soup.find(id= feature[4])["xlink:href"]=''



                #soup.find(id= 'blackrect').decompose()
                #########Issaugom pakeista svg
                file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
                file1 = drive.CreateFile({'title': svgname+'.svg',
                                        'parents': [{
                                        'id': SvgFolderID
                                        }]
                                        })  # Create GoogleDriveFile instance with title 'Hello.txt'.
                file1.SetContentString(soup)####soup.prettify()
                file1.Upload()

        OrderStatusManagementfilename=a[22]+'MANAGEMENT.txt'
        orderedproductsdata=json.dumps(orderedproductsdata)######################ikeliam lysna faila kuriame nurodyta uzsakymo sudetis ir busenos
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        file1 = drive.CreateFile({'title': OrderStatusManagementfilename,
                                'parents': [{
                                'id': EshopOrderdatatxtfilesID
                                }]
                                })
        file1.SetContentString(orderedproductsdata)
        file1.Upload()

        ######pagrindiniame orderliste pazymim statusa i SVG's generated
        orderidlist=sheet.col_values(1)
        for e in range(1, len(orderidlist)):
            if str(a[0]) in str(orderidlist[e]):
                sheet.update_cell(e+1, 3, "SVG's generated")
                break

    return soup










def getorderexelrowsandsvgs(orderlist):######grazina dicta {productid:'svg innerhtml'}  +SUKURIA NAUJUS SVG


    orderlist_file=orderlistfile
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    client=gspread.authorize(credentials)
    date=datetime.datetime.now()
    sheet=client.open_by_key(orderlist_file)
    sheet=sheet.worksheet('orders')



    orderlistfiltered=[]
    orderidlist=sheet.col_values(1)
    strorderlist=[str(i) for i in orderlist]
    listrange=len(orderidlist)
    orderlistfiltered=[]

    ######################################sudarom lista is pasirinktu orders listo numeriu
    for a in range(1, listrange):
        if str(orderidlist[a]) in strorderlist:
            orderlistfiltered.append(a+1)

    finallist=[]
    #########################sudarom pasirinktu uzsakymu info lista
    for a in orderlistfiltered:
        finallist.append(sheet.row_values(a))


    return finallist












######################################################################################3
#################################3ĘĘĘXĘĘĘĘĘĘĘĘĘĘĘĘĘĘ££££££££££££££££££££££££££££££££££££££££££££££££333


def getordersvgs1(order):##### paima orderlista grazina img pathus


    filename=order[0][22]+"MANAGEMENT.txt"

    if order[0][2]=='finished':
        listfolderid="'"+EshopOrderdatatxtfilesFinishedID+"'"
    else:
        listfolderid="'"+EshopOrderdatatxtfilesID+"'"

        ##order id=[22]
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': listfolderid+" in parents and trashed=false"}).GetList()

    for file1 in file_list:
        if file1['title']==filename:
            svglistfileid=file1['id']

    file = drive.CreateFile({'id': svglistfileid})
    file.GetContentFile('shop/tmp/orderdict.txt')
    with open('shop/tmp/orderdict.txt', 'r') as u:
            ordersvgslist=json.loads(u.read())




    ############### I BEVEIK PARUOSTA DICTA VIETOJE 'svgname' svg vardo ikeliame svg turini

    SvgProcessedFolderList = drive.ListFile({'q': "'"+SvgProcessedFolderID+"'"+" in parents and trashed=false"}).GetList()
    SvgFolderList = drive.ListFile({'q': "'"+SvgFolderID+"'"+" in parents and trashed=false"}).GetList()
    for a in ordersvgslist:
        svgproductid=ordersvgslist[a]['product id']
        picturename=getproductinfo(svgproductid)['photos'][0]
        ordersvgslist[a]['svgfile']=picturename

    return ordersvgslist



#################################################################################################3
############################################################################################3















def getordersvgs(order):##### paima orderlista grazina svg failu id


    filename=order[0][22]+"MANAGEMENT.txt"

    if order[0][2]=='finished':
        listfolderid="'"+EshopOrderdatatxtfilesFinishedID+"'"
    else:
        listfolderid="'"+EshopOrderdatatxtfilesID+"'"

        ##order id=[22]
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': listfolderid+" in parents and trashed=false"}).GetList()

    for file1 in file_list:
        if file1['title']==filename:
            svglistfileid=file1['id']

    file = drive.CreateFile({'id': svglistfileid})
    file.GetContentFile('shop/tmp/orderdict.txt')
    with open('shop/tmp/orderdict.txt', 'r') as u:
            ordersvgslist=json.loads(u.read())




    ############### I BEVEIK PARUOSTA DICTA VIETOJE 'svgname' svg vardo ikeliame svg turini

    SvgProcessedFolderList = drive.ListFile({'q': "'"+SvgProcessedFolderID+"'"+" in parents and trashed=false"}).GetList()
    SvgFolderList = drive.ListFile({'q': "'"+SvgFolderID+"'"+" in parents and trashed=false"}).GetList()
    for a in ordersvgslist:
        svgname=ordersvgslist[a]['svgname']
        for file in SvgFolderList:
            if file['title']==svgname:
                file1 = drive.CreateFile({'id': file['id']})
                file1.GetContentFile('shop/tmp/orderdict.txt')
                with open('shop/tmp/orderdict.txt', 'r') as u:
                    ordersvgslist[a]['svgfile']=u.read()

        for file in SvgProcessedFolderList:
            if file['title']==svgname:
                file1 = drive.CreateFile({'id': file['id']})
                file1.GetContentFile('shop/tmp/orderdict.txt')
                with open('shop/tmp/orderdict.txt', 'r') as u:
                    ordersvgslist[a]['svgfile']=u.read()

    return ordersvgslist






def setSvgsFinished(order, finishedsvgs):
    filename=order[0][22]+"MANAGEMENT.txt"

    if order[0][2]=='finished':
        listfolderid="'"+EshopOrderdatatxtfilesFinishedID+"'"
    else:
        listfolderid="'"+EshopOrderdatatxtfilesID+"'"

        ##order id=[22]
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': listfolderid+" in parents and trashed=false"}).GetList()

    for file1 in file_list:
        if file1['title']==filename:
            svglistfileid=file1['id']

    file = drive.CreateFile({'id': svglistfileid})
    file.GetContentFile(tmpfolderdest+'orderdict.txt')
    with open(tmpfolderdest+'orderdict.txt', 'r') as u:
            ordersvgslist=json.loads(u.read())

    svglistinmainfolder = drive.ListFile({'q': "'"+SvgFolderID+"'"+" in parents and trashed=false"}).GetList()
    svglistinInkscapePreparedfolder = drive.ListFile({'q': "'"+SvgInkscapePreparedFolderID+"'"+" in parents and trashed=false"}).GetList()
    svglistinProcessedfolder = drive.ListFile({'q': "'"+SvgProcessedFolderID+"'"+" in parents and trashed=false"}).GetList()
    alsvgs=svglistinProcessedfolder+svglistinInkscapePreparedfolder+svglistinmainfolder


    for a in finishedsvgs:
        ordersvgslist[a]['status']='finished'

        for file1 in alsvgs:####################Perkeliam pagaminta svg i finished folderi
            if file1['title']==a:

                file1['parents']=[{'id': SvgFinishedFolderID}]
                file1.Upload() # Update metadata.


    ordersvgslist=json.dumps(ordersvgslist)
    file.SetContentString(ordersvgslist)
    file.Upload()

    return ordersvgslist


def setorderspayed(transactionsmslist):

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)

    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')
    orderidlist=sheet.col_values(1)
    ordercost=sheet.col_values(7)
    paystatus=sheet.col_values(3)
    errors=[]
    looprange=range(1, len(orderidlist))
    paymentsinorderlist=[]
    for a in transactionsmslist:#####################dalinam i atskirus uzsakymus
        for e in looprange:
            try:
                if str(orderidlist[e].lower()) in str(a).lower():
                    paymentsinorderlist.append(str(a))
                    if paystatus[e]=='unpayed':#########################Jei unpaid darom apmokejima
                        pFrom = a.index("+") + 1;
                        pTo = a.index("EUR Mokėtojas");
                        paid = a[pFrom:pTo]
                        paid=float(paid)*100
                        sheet.update_cell(e+1, 20, paid)
                        if paid==int(ordercost[e+1]):
                            sheet.update_cell(e+1, 3, "payed")
                        elif paid<int(ordercost[e+1]):
                            sheet.update_cell(e+1, 3, "not enough paid")
                            errors.append('Not enough paid: '+str(orderidlist[e])+'    SMS: '+str(a))
                        elif paid>int(ordercost[e+1]):
                            sheet.update_cell(e+1, 3, "overpaid")
                            errors.append('overpaid: '+str(orderidlist[e])+'    SMS: '+str(a))
                        orderdata=getorderdatabyid(e)
                        a=generateandsendinvoice(orderdata)
                        #return str(getfilejsonfromdrive(orderdata['order dict fileID']))
                    #else:SITA GALIMA BUS IJUNGT JEI PADARYSIU KAD ISTRINTU PAVEDIMU SMS SU PATVIRTINTAIS paid
                     #   errors.append('Dublicated payment: '+str(a))
                    elif paystatus[e]!='unpayed':       ##########################jei apmoketa tada dadedam nauja suma prie senos
                        errors.append('dublicated payment for order: '+str(orderidlist[e])+'    SMS: '+str(a))

                    break
                ###jei yra erroras issaugau liste kuris bus issaugotas erroru loge
                if e==looprange[-1]:
                    errors.append('no order for incomming transaction: '+str(a))
            except Exception as e:
                errors.append('some system payment error: '+str(e))

    addpaymentstopaymentsfile(paymentsinorderlist)
    if len(errors)>0:
        addpaymenterrors(errors)
        return errors
    return 'OK'




















def checkandaddpaymentsfromsms(transactionsmslist):#####NAUDOJA telefono visus sms nuo swedbank. Jei nera sms'o spreadsheete, ideda smsa i payments spreadshyta

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(paymentsfile)
    sheet=sheet.worksheet('Sheet1')
    paymentslist=sheet.col_values(2)

    for a in transactionsmslist:
        if a not in paymentslist:
            sheet.append_row([str(datetime.datetime.now()), a, 'Got sms'])
    return 'OK'




def SETordersPAYED(smspaymentslist):#####NAUDOJA telefono visus sms nuo swedbank. Jei nera sms'o spreadsheete, ideda smsa i payments spreadshyta
    unpaidorderlist=getFileDotJson(unpaidordersjsonID)
    smspaymentslist=smspaymentslist

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')

    errors=[]
    SmsListMarkedAsConfirmed=[]
    orderstosendinvoice=[]
    for a in smspaymentslist:
        if a[2]=='Not confirmed':
            for e in unpaidorderlist:
                try:
                    if str(e[0].lower()) in str(a[0]).lower():
                            pFrom = a[0].index("+") + 1;

                            pTo = a[0].index("EUR Mokėtojas");
                            paid = a[0][pFrom:pTo]
                            paid=float(paid)*100

                            newrowinorderlist=e
                            newrowinorderlist[19]=paid
                            if paid==int(e[6]):
                                newrowinorderlist[2]='payed'
                                sheet.append_row(newrowinorderlist)
                                orderstosendinvoice.append(newrowinorderlist)
                                newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')

                            elif paid<int(e[6]):
                                newrowinorderlist[2]="not enough paid"
                                sheet.append_row(newrowinorderlist)
                                errors.append('Not enough paid: '+str(e[0])+'    SMS: '+str(a[0]))
                                newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')
                            elif paid>int(e[6]):
                                newrowinorderlist[2]="overpaid"
                                errors.append('Overpaid: '+str(e[0])+'    SMS: '+str(a[0]))
                                sheet.append_row(newrowinorderlist)
                                orderstosendinvoice.append(newrowinorderlist)
                                newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')

                            SmsListMarkedAsConfirmed.append(a)
                            #orderdata=getorderdatabyid(e)
                            #a=generateandsendinvoice(orderdata)
                            #return str(getfilejsonfromdrive(orderdata['order dict fileID']))
                        #else:SITA GALIMA BUS IJUNGT JEI PADARYSIU KAD ISTRINTU PAVEDIMU SMS SU PATVIRTINTAIS paid
                         #   errors.append('Dublicated payment: '+str(a))
                            break

                    ###jei yra erroras issaugau liste kuris bus issaugotas erroru loge
                    if e==unpaidorderlist[-1]:
                        errors.append('no order for incomming transaction: '+str(a[0]))
                        SmsListMarkedAsConfirmed.append(a)

                except Exception as e:
                    SmsListMarkedAsConfirmed.append(a)
                    errors.append('some system payment error: '+str(e))

    if len(SmsListMarkedAsConfirmed)>0:
        for q in SmsListMarkedAsConfirmed:
            smspaymentslist[smspaymentslist.index(q)][2]='Seen'

        jsonnewsmslist=json.dumps(smspaymentslist, indent=4)
        file1 = drive.CreateFile({'id': SwedbankPaymentsID})
        file1.SetContentString(jsonnewsmslist)
        file1.Upload()


    if len(errors)>0:
        sheet=client.open_by_key(paymenterrors)
        sheet=sheet.worksheet('Sheet1')
        sheeterrorlist=sheet.col_values(1)
        for a in errors:

            if a not in sheeterrorlist:
                row=[a, str(datetime.datetime.now())]
                sheet.append_row(row)

    return orderstosendinvoice









def addordertoordersheet(smspaymentslist):#####NAUDOJA telefono visus sms nuo swedbank. Jei nera sms'o spreadsheete, ideda smsa i payments spreadshyta
    unpaidorderlist=getFileDotJson(unpaidordersjsonID)
    smspaymentslist=smspaymentslist

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')

    errors=[]
    orderstosendinvoice=[]
    for a in smspaymentslist:
        for e in unpaidorderlist:
            try:
                if str(e[0].lower()) in str(a[0]).lower():
                        paid=int(a[1])

                        newrowinorderlist=e
                        newrowinorderlist[19]=paid
                        if paid==int(e[6]):
                            newrowinorderlist[2]='payed'
                            sheet.append_row(newrowinorderlist)
                            orderstosendinvoice.append(newrowinorderlist)
                            newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')

                        elif paid<int(e[6]):
                            newrowinorderlist[2]="not enough paid"
                            sheet.append_row(newrowinorderlist)
                            newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')
                        elif paid>int(e[6]):
                            newrowinorderlist[2]="overpaid"
                            sheet.append_row(newrowinorderlist)
                            newrowinorderlist[20]=datetime.datetime.now().strftime('%Y-%m-%d')
                        break

                if e==unpaidorderlist[-1]:
                    return 'no order:'+str(a[0])

            except Exception as e:
                return 'error while importing order: '+str(e)
    return 'OK'













































def manageSMSpaymentdata(smslist):  #####NAUDOJA telefono visus sms nuo swedbank. Jei nera sms'o spreadsheete, ideda smsa i payments spreadshyta
    try:
        oldsmslist=getFileDotJson(SwedbankPaymentsID)################failas kuriame yra visi sms
        unpaidorderslist=getFileDotJson(unpaidordersjsonID)##############failas kuriame visi neapmoketi uzsakymai
        newsmslist=oldsmslist

        for a in smslist:
            stringifiedsmslist=str(oldsmslist)
            if a.lower() not in stringifiedsmslist.lower():
                suggestion='No suggestion'
                for order in unpaidorderslist:
                    if order[0].lower() in a.lower():
                        suggestion=order[0]
                newsmslist.append([a, suggestion, 'Not confirmed'])
        if len(newsmslist)!=oldsmslist:#######################jei atejo naujas sms irasyti i sms sarasa
            scope=['https://www.googleapis.com/auth/drive']
            credentials= ServiceAccountCredentials.from_json_keyfile_name(credentialsfile, scope)
            gauth = GoogleAuth()
            gauth.credentials = credentials
            drive = GoogleDrive(gauth)

            jsonnewsmslist=json.dumps(newsmslist, indent=4)
            file1 = drive.CreateFile({'id': SwedbankPaymentsID})
            file1.SetContentString(jsonnewsmslist)
            file1.Upload()
    except Exception as e:
        return e
    return newsmslist










def getFileDotJson(id):
        scope=['https://www.googleapis.com/auth/drive']
        credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        currentToollist = drive.CreateFile({'id': id})
        currentToollist.GetContentFile(serverfolder+'/tmp/tmpjson.json')
        with open(serverfolder+'/tmp/tmpjson.json', 'r') as u:
            jsonfile=json.loads(u.read())
        return jsonfile







def addpaymentstopaymentsfile(paymentslist):
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(paymentsfile)
    sheet=sheet.worksheet('Sheet1')
    counter=0
    for a in paymentslist:
        sheet.append_row([str(datetime.datetime.now()), a])



def addpaymenterrors(errorlist):
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)

    sheet=client.open_by_key(paymenterrors)
    sheet=sheet.worksheet('Sheet1')
    sheeterrorlist=sheet.col_values(1)
    sheeterrorcounterlist=sheet.col_values(3)

    counter=0
    for a in errorlist:
        counter+=1
        if a not in sheeterrorlist:
            row=[a, 'on', '1', str(datetime.datetime.now())]
            sheet.append_row(row)
        elif a in sheeterrorlist:###########################jei pasikartojo eroras updatinam jo eilute
            rowindex=sheeterrorlist.index(a)
            currenterrorcounter=int(sheeterrorcounterlist[rowindex])
            sheet.update_cell(rowindex+1, 3, currenterrorcounter+1)#####skaiciuojam ir updatinam kiek kartu iviko sis error
            sheet.update_cell(rowindex+1, 4, str(datetime.datetime.now()))#####updatinam paskutinio erroro data



def getfilejsonfromdrive(fileid):###################################VEIKIA TIK SU TXT FAILAIS KURIUOSE IRASYTAS JSON
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)

    file = drive.CreateFile({'id': fileid})
    file.GetContentFile('shop/tmp/orderdict.txt')
    with open('shop/tmp/orderdict.txt', 'r') as u:
        userdict=u.readlines()
    userdict=json.loads(userdict[0])
    return userdict


def getorderdatabyid(num):
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')
    orderdataids={'id':1, 'order date':2, 'order status':3, 'buyer type':4, 'name':5, 'bank number':6, 'amount(cents)':7, 'email':8, 'phone':9, 'organization':10, 'organization address':11, 'organization id':12, 'pvm id':13, 'delivery type':14, 'omniva address':15, 'address':16, 'city':17, 'zip code': 18, 'order dict filename':23, 'order dict fileID':24}
    orderdata={}
    orderdata['order date']=sheet.col_values(2)[num]
    for feature in orderdataids:
        try:
            orderdata[feature]=sheet.col_values(orderdataids[feature])[num]
        except Exception as e:
            return feature

    #    q=q[num]
    #    orderdata[feature]=num

    return orderdata

def generateandsendinvoice(userdata):
    userdict=getfilejsonfromdrive(userdata['order dict fileID'])
    cartdata=getpricelistfromuserdict(userdict)
    cartlist=[]
    for a in cartdata:
        singleproduct={}
        singleproduct['name']=a['productname']
        singleproduct['id']=a['productid']
        if a['discount']==0:
            singleproduct['price']=a['price']
        else:
            singleproduct['price']=a['discount']
        singleproduct['number']=a['productnumber']
        singleproduct['fullprice']=int(singleproduct['number'])*int(singleproduct['price'])
        cartlist.append(singleproduct)
    cartdata={'orderid':userdata['id'], 'cartprice':userdata['amount(cents)'], 'deliverytype':userdata['delivery type'], 'deliveryprice':deliveryprices['ltu'][userdata['delivery type']], 'cartlist':cartlist}
    buyerdata={'buyer type':userdata['buyer type'], 'name':userdata['name'], 'email':userdata['email'], 'phone':userdata['phone'], 'delivery type':userdata['delivery type'], 'omniva address':userdata['omniva address'], 'address':userdata['address'], 'organization name': userdata['organization'], 'organization id':userdata['organization id'], 'pvm id':userdata['pvm id'], 'organization address':userdata['organization address']}
    invoicehtml = render_template('invoice/PreInvoice.html', seller=seller, cartdata=cartdata, buyerdata=buyerdata )
#    ###/pdf
#
    pdf = HTML(string=invoicehtml).write_pdf('shop/tmp/preinvoice.pdf')
    h3='Sveiki, '+buyerdata['name']+','
    emailhtml=render_template('email templates/order.html', fullprice=userdata['amount(cents)'],h3=h3, shopname=shopname, seller=seller, ordernumber=userdata['id'])
    return emailhtml


def getordernumber(orderid):######grazina dicta {productid:'svg innerhtml'}  +SUKURIA NAUJUS SVG


    orderlist_file=orderlistfile
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    client=gspread.authorize(credentials)
    date=datetime.datetime.now()
    sheet=client.open_by_key(orderlist_file)
    sheet=sheet.worksheet('orders')

    orderidlist=sheet.col_values(1)
    listrange=len(orderidlist)

    ######################################sudarom lista is pasirinktu orders listo numeriu
    for a in range(1, listrange):
        if orderid in str(orderidlist[a]):
            return a



def makesvgssetnewproduct():

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)

    with open('shop/templates/svgs/'+ singleproduct['productid'] +'mf'+'.svg','r') as soup:
        soup = BeautifulSoup(soup.read(), features ='xml')
    svgdatalist={'orderid':orderid, 'product id':singleproduct['productid'], 'svg':soup, 'material':prinfo['material'], 'thickness':prinfo['thickness'], 'width':prinfo['width'], 'height':prinfo['height'], 'price':prinfo['price'], 'weight':prinfo['weight']}
    for everysinglesvggenerator in singleproduct['productlist']:
        svgname='OrderId='+str(orderid)+', product='+str(productcounter)+', material='+prinfo['material']+prinfo['thickness']+', price='+prinfo['price']

        orderedproductsdata[svgname+'.svg']={'product id':singleproduct['productid'], 'svgname':svgname+'.svg',
                            'material':prinfo['material'], 'thickness':prinfo['thickness'], 'width':prinfo['width'],
                            'height':prinfo['height'], 'price':prinfo['price'], 'weight':prinfo['weight'], 'inputdata':singleproduct['productlist'], 'status':'SVG only generated','Who is manufacturing':'Noone yet'}

        soup.find(id= 'orderid').string=str(orderid)
        productcounter+=1
        for feature in productinfoinputs:######Loopinam per svg pakeiciamus laukelius ir ikeliam userio inputus
            if feature[2]=='text':
                soup.find(id= feature[4]).string=everysinglesvggenerator[feature[1]]
            if feature[2]=='img':
                if everysinglesvggenerator[feature[1]] in singleproduct['imglist']:
                    soup.find(id= feature[4])["xlink:href"]= singleproduct['imglist'][everysinglesvggenerator[feature[1]]]
                else:
                    soup.find(id= feature[4])["xlink:href"]=''



        #soup.find(id= 'blackrect').decompose()
        ########Issaugom pakeista svg
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        file1 = drive.CreateFile({'title': svgname+'.svg',
                                'parents': [{
                                'id': SvgFolderID
                                }]
                                })  # Create GoogleDriveFile instance with title 'Hello.txt'.
        file1.SetContentString(soup)####soup.prettify()
        file1.Upload()

        OrderStatusManagementfilename=a[22]+'MANAGEMENT.txt'
        orderedproductsdata=json.dumps(orderedproductsdata)######################ikeliam lysna faila kuriame nurodyta uzsakymo sudetis ir busenos
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        file1 = drive.CreateFile({'title': OrderStatusManagementfilename,
                                'parents': [{
                                'id': EshopOrderdatatxtfilesID
                                }]
                                })
        file1.SetContentString(orderedproductsdata)
        file1.Upload()

        ######pagrindiniame orderliste pazymim statusa i SVG's generated
        orderidlist=sheet.col_values(1)


    return soup






def storeinvoiceidanddate(orderid, invoicedate, invoiceid):

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    client=gspread.authorize(credentials)
    sheet=client.open_by_key(orderlistfile)
    sheet=sheet.worksheet('orders')
    orderidlist=sheet.col_values(1)
    ordercost=sheet.col_values(7)
    paystatus=sheet.col_values(3)
    errors=[]
    looprange=range(1, len(orderidlist))
    paymentsinorderlist=[]

    for e in looprange:
        if str(orderidlist[e].lower()) in str(orderid).lower():
            sheet.update_cell(e+1, 21, invoicedate)
            sheet.update_cell(e+1, 22, invoiceid)
    return 'OK'

