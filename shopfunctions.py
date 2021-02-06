from passlib.hash import sha256_crypt
from flask import Flask, flash, session, request
import gc
import random
app= Flask(__name__)
from ZODB import FileStorage, DB
import transaction
import csv
from math import ceil as roundup
import jwt
from opcv import handleimgsandtext
import cv2
from werkzeug import secure_filename
import datetime
import os
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import stripe
import json

unpaidorderGoogleDrivefileID='ID OF THE FILE'
EshopOrderdatatxtfilesID=os.environ.get('googlediscfolderid_orders/orderdatatxtfiles')
orderlistfileid=os.environ.get("googledisc_orders/orderlist")
serverfolder= os.environ.get("directories_eshopdir")
credentialsfile=serverfolder+'/creds.json'
deliveryprices={'ltu':{'Omniva':315, 'LPregistered':223}}
prperpage=35 ####### Nustatau produktu skaiciu vienam puslapiui

unpaidordersjsonID = os.getenv("googledisc_orders/unpaidordersJson")
secretkey=os.getenv("jwt_secretcode")
ALLOWED_IMG_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'bmp','gif']
directories={'tmp':serverfolder+"/tmp/"}
stripe_keys = {
  'secret_key': 'YOUR STRIPE SECRET KEY',
  'publishable_key': 'YOUR STRIPE PUBLISHABLE KEY'
    }


storage = FileStorage.FileStorage('shop/database/database.fs')
db = DB(storage)
connection = db.open()
root = connection.root()



##########################Produkto info vietos CSV faile:
def productinfo(key):
    products={'prid':0,
    'prname':1,
    'prprice':2,
    'prdiscount':3,
    'prdescription':6,
    'prmaterial':7,
    'prwidth':8,
    'prheight':9,
    'prthickness':10,
    'prweight':11,
    'prcategory':12,
    'prcategory2':13,
    'prcategory3':14,
    'prsimilarproducts':15,
    'prkeywords':16,
    'prinputinfo':17,
    'prplaceholder':18,
    'printerestsclass':19,
    'prmaterial1':20,
    'prmat1consumption':21,
    'prmaterial2':22,
    'prmat2consumption':23,
    'prmaterial3':24,
    'prmat3consumption':25,
    'prmakettime':26,
    'prcnctime':27,
    'prlasertime':28,
    'prhandworktime':29,
    'prphoto1':30,
    'prphoto2':31,
    'prphoto3':32,
    'prphoto4':33,
    'prphoto5':34,
    'prphoto6':35,
    'prphoto7':36,
    'prphoto8':37,
    'prphoto9':38,
    'prphoto10':39,
    'configuratortype':40,
    'prtype':41}
    return products[key]




def csvcategories():
    with open("shop/categories.csv") as u:
        kategorijos=csv.reader(u)
        kategorijos = [r for r in kategorijos]
        categories={}
    for a in kategorijos:
        categories[a[0]]=a[1:]
    return categories



############SHOPPING CART:
def cartproductsinfo(productlist):
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    returnlist=[]
    for n in productlist:
        returnlist.extend([[prekes[(int(n)-1)][productinfo('prname')], prekes[(int(n)-1)][productinfo('prphoto1')], prekes[(int(n)-1)][productinfo('prprice')], prekes[(int(n)-1)][productinfo('prdiscount')], prekes[(int(n)-1)][productinfo('prid')], prekes[(int(n)-1)][productinfo('prtype')]]])
    return returnlist
##################################





#####################SUGGEST SIMILAR PRODUCTS
def suggestsimilarproducts(similarpr):
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    offs=[["prsimilarproducts", prekes[(int(similarpr)-1)][productinfo("prsimilarproducts")], "Panašūs produktai"],["printerestsclass", prekes[(int(similarpr)-1)][productinfo("printerestsclass")], "Siūlome taip pat peržiūrėti"]]
    resultdict={}
    productlist=allproductsidlist()
    for offer in offs:
        resultdict[offer[1]]=[]
        #####################Atranka pagal bruoza ir jo turini
        for id in productlist:
            if offer[1] in prekes[(int(id)-1)][productinfo(offer[0])]:
                if id not in resultdict[offer[1]]:
                    if str(id)!=str(similarpr):                             ###padarau kad nesiulytu tos pacios prekes kuri yra atidaryta
                        resultdict[offer[1]].extend([id])
    newresultdict={}

    for a in resultdict:
        resultdictnumber=3
        if len(resultdict[a])<3:
            resultdictnumber=len(resultdict[a])
        newresultdict[a]=random.sample(resultdict[a], resultdictnumber)    #####kad nebutu klaidos ir nebandytu imti daugiau random variantu jei yra mazai is ko rinktis
    newresultdict1={}

    for a in newresultdict:
        newresultdict1[a]=pagesfnc(1, newresultdict[a], prekes)
    for a in offs:
        newresultdict1[a[1]].extend([a[2]])
        newresultdict1[a[1]].extend([a[0]])
    return newresultdict1


#####################SUGGEST PRODUCT DALYKAI MAIN PAGE
def suggestproducts():
    with open("shop/mainpageoffers.csv") as i:
        offs=csv.reader(i)
        next(offs)
        offs=[r for r in offs]
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    resultdict={}
    productlist=allproductsidlist()
    for offer in offs:
        resultdict[offer[1]]=[]
        #####################Atranka pagal bruoza ir jo turini
        for id in productlist:
            if offer[1] in prekes[(int(id)-1)][productinfo(offer[0])]:
                if id not in resultdict[offer[1]]:
                    resultdict[offer[1]].extend([id])
    newresultdict={}
    for a in resultdict:
        newresultdict[a]=random.sample(resultdict[a], 3)
    newresultdict1={}
    for a in newresultdict:
        newresultdict1[a]=pagesfnc(1, newresultdict[a], prekes)
    for a in offs:
        newresultdict1[a[1]].extend([a[2]])
        newresultdict1[a[1]].extend([a[0]])
    return newresultdict1



#####################PREKIU PAIESKA
def searchfnc(page , keywordsx, kategorijax, medziagax, nuox, ikix, interestsx, similarproductsx):
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    resultlist=[]
    newresultlist=[]
    keywordsmessage=keywordsx #######islaikau orginalius keywords su į,š,ų.. jei reiktų pranešti vartotojui apie netinkamą keyword
    if len(keywordsx)!=0:
        keywordsx=keywordsx.replace("ą", "a")
        keywordsx=keywordsx.replace("č", "c")
        keywordsx=keywordsx.replace("ę", "e")
        keywordsx=keywordsx.replace("ė", "e")
        keywordsx=keywordsx.replace("į", "i")
        keywordsx=keywordsx.replace("š", "s")
        keywordsx=keywordsx.replace("ų", "u")
        keywordsx=keywordsx.replace("ū", "u")
        keywordsx=keywordsx.replace("ž", "z")
        keywordsx=keywordsx.replace(",", " ")
        keywordsx=keywordsx.replace(".", " ")
        keywordsx=keywordsx.replace("'", " ")
        keywordsx=keywordsx.replace('"', " ")
        keywordsx=keywordsx.replace('-', " ")
        keywordsx=keywordsx.replace('#', " ")
        keywordslist=keywordsx.split()
        maxkeycounter=0
        for eilesnr in prekes:
            counter=0
            for key in keywordslist:
                if key.lower() in eilesnr[productinfo('prkeywords')].lower():
                    counter+=1
                    if counter==1:
                        resultlist.extend([[eilesnr[0], counter]])
                    if counter>1:
                        resultlist[-1]=[eilesnr[0], counter]
                    if counter>maxkeycounter:
                        maxkeycounter=counter
    #########Padarau paieskos atitikmenu lista is eiles pagal tai ar daug atitiko keywordu
        while True:
            if maxkeycounter==0:
                break
            for a in resultlist:
                if a[1]==maxkeycounter:
                        newresultlist.extend([a[0]])
            maxkeycounter-=1
        if newresultlist==[]:
            flash("Prekių pagal raktažodį " +keywordsmessage+ " nerasta!")
            newresultlist3=[]
            return {"pages": pagesfnc(page, newresultlist3, prekes), "pagination": paginationfnc(page, len(newresultlist3))}
    #############JEI NERA RAKTAZODZIO DAROMAS ELSE
    else:
        newresultlist=allproductsidlist()
    newresultlist1=[]
    #####################Atranka pagal pasirinktas kategorijas
    if kategorijax!=[]:
        for id in newresultlist:
            for kat in kategorijax:
                if kat in prekes[(int(id)-1)][productinfo('prcategory')]:
                    if id not in newresultlist1:
                        newresultlist1.extend([id])
        ##jei nera rezultatu grazina visas prekes+zinute vartotojui
        if newresultlist1==[]:
            if len(keywordsx)==0:
                flash("Kategorijose "+str(kategorijax)+" nerasta rezultatų")
            else:
                flash("Kategorijose "+str(kategorijax)+" pagal įvestą raktažodį nerasta prekių")
            newresultlist3=[]
            return {"pages": pagesfnc(page, newresultlist3, prekes), "pagination": paginationfnc(page, len(newresultlist3))}
    else:
        newresultlist1=newresultlist
        #############################Atranka pagal produkto medžiagą
    newresultlist2=[]
    if medziagax!=[]:
        for id in newresultlist1:
            for mat in medziagax:
                if mat in prekes[(int(id)-1)][productinfo('prmaterial')]:
                    if id not in newresultlist2:
                        newresultlist2.extend([id])
        ##jei nera rezultatu grazina visas prekes+zinute vartotojui
        if newresultlist2==[]:
            newresultlist3=[]
            flash('Pagal pasirinktus paieškos parametrus prekių nerasta.')
            return {"pages": pagesfnc(page, newresultlist3, prekes), "pagination": paginationfnc(page, len(newresultlist3))}
    else:
        newresultlist2=newresultlist1
    #############################Atranka pagal produkto kainą
    newresultlist3=[]
    if len(nuox)==0  and len(ikix)==0:    #jei neivesta kaina grazinu paskutini paieskos rezultata baigdamas funkcija
        newresultlist3=newresultlist2        #patikrinu ar dar nera nurodyti interesai

    else:
        if len(nuox)==0:  #jei nieko neivesta i laukeli priskiriu reiksme 0
            nuox=0
        else:
            try:
                nuox=int(nuox)*100
            except ValueError:  ####jei iraso ne skaitmenis priskiriu reiksme nuliui
                nuox=0
        if len(ikix)==0: #jei nieko neivesta i laukeli priskiriu reiksme dideliai sumai
            ikix=9999999
        else:
            try:
                ikix=int(ikix)*100
            except ValueError:  ####jei iraso ne skaitmenis priskiriu reiksme dideliai sumai
                ikix=99999999999
        for id in newresultlist2:
            if nuox<=int(prekes[(int(id)-1)][productinfo('prprice')])<=ikix:
                    newresultlist3.extend([id])

        ##jei nera rezultatu grazina visas prekes+zinute vartotojui
        if newresultlist3==[]:
            newresultlist3=newresultlist2
            flash("Pagal pasirinktą kainą prekių nerasta")
    newresultlist4=[]
    if len(interestsx)!=0:########patikrinam ar nereikia atrinkti rezultato pagal interesu klases
        for id in newresultlist3:
            if interestsx in prekes[(int(id)-1)][productinfo('printerestsclass')]:
                if id not in newresultlist4:
                    newresultlist4.extend([id])
        newresultlist3=newresultlist4

    if len(similarproductsx)!=0:########patikrinam ar nereikia atrinkti rezultato pagal interestu klases
        newresultlist4=[]
        for id in newresultlist3:
            if similarproductsx in prekes[(int(id)-1)][productinfo('prsimilarproducts')]:
                if id not in newresultlist4:
                    newresultlist4.extend([id])
            else:
                if id in newresultlist4:
                    newresultlist4.remove(id)


        newresultlist3=newresultlist4
    if newresultlist3==[]:
            newresultlist3=[]
            flash("Pagal pasirinktą kainą prekių nerasta")

    return {"pages": pagesfnc(page, newresultlist3, prekes), "pagination": paginationfnc(page, len(newresultlist3))}
###################################################################################################


###Funkcija grazinanti tik vieno puslapio prekiu sarasa su reikalinga info
def pagesfnc(page, plist, prekes):
    currentpagelist1=[]
    for a in plist:
        currentpagelist1.extend([[prekes[(int(a)-1)][productinfo('prname')], prekes[(int(a)-1)][productinfo('prprice')],
        prekes[(int(a)-1)][productinfo('prdiscount')], prekes[(int(a)-1)][0],prekes[(int(a)-1)][productinfo('prphoto1')]]])
    currentpagelist1=currentpagelist1[(int(page)*prperpage-prperpage):(int(page)*prperpage)]
    return currentpagelist1

#### Funkcija grazina gretimu puslapiu sarasa (pagination)
def paginationfnc(pagetopost, lenproductlist):
    pagesnumber=lenproductlist/prperpage
    pagesnumber=roundup(pagesnumber)
    return pagesnumber

#####Funkcija grazina visu produktu id sarasa
def allproductsidlist():
    with open("shop/products.csv") as u:
            all1=csv.reader(u)
            next(all1)
            all1=[r for r in all1]
    all2=[]
    for a in all1:
        all2.extend([a[0]])
    return all2

######################## Produkto info pateikimas

def getproductinfo(productid):
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    for a in prekes:
        if a[0]==productid:
            infodict={"name":a[productinfo("prname")], "price":a[productinfo("prprice")], "discount":a[productinfo("prdiscount")],
                        "description":a[productinfo("prdescription")], "material":a[productinfo('prmaterial')], "width":a[productinfo("prwidth")],
                        "height":a[productinfo("prheight")], "thickness":a[productinfo("prthickness")], "weight":a[productinfo("prweight")],
                        "inputinfo":a[productinfo('prinputinfo')], "inputinfo":a[productinfo('prinputinfo')], "placeholder":a[productinfo('prplaceholder')],
                        "photos":[a[productinfo('prphoto1')], a[productinfo('prphoto2')], a[productinfo('prphoto3')], a[productinfo('prphoto4')], a[productinfo('prphoto5')],a[productinfo('prphoto6')],a[productinfo('prphoto7')], a[productinfo('prphoto8')],a[productinfo('prphoto9')],a[productinfo('prphoto10')]],
                        "categories":a[productinfo('prcategory')], 'type':a[productinfo('prtype')], 'configuratortype':a[productinfo('configuratortype')]
                        }
            infodict['categories']=infodict['categories'].split(',')
            return infodict


#####################Neregistruotu useriu sausainis
def checkforcookies():
    if session.logged_in:
        flash("NOT LOGGED IN")


#####################REGISTRACIJOS DALYKAI
def registerfnc(a, b, g, h):
    register_arguments=[True, True, True]
    a=sha256_crypt.encrypt(str(a))
    if len(str(g))>40:
        register_arguments[1] = False
        flash("Įvestas pašto adresas yra per ilgas")
    else:
        if g in root['users']:
            register_arguments[0]=False
            flash('Jūsų pasirinktas pašto adresas jau yra užregistruotas. Bandykite prisijungti arba atnaujinkite slaptažodį.')
    if sha256_crypt.verify(b, a) == False:
        register_arguments[2]= False
        flash("Neteisingai pakartojote slaptažodį.")
    if register_arguments==[True, True, True]:
        root['users'][g]={'pwd': a, 'getoffers':h, 'cart':[], 'liked':[]}
        flash("Vartotojas "+str(g)+" sėkmingai sukurtas")
        root._p_changed=True
        transaction.commit()
        gc.collect()
        return "ok"
    else:
        c.close()
        conn.close()
        gc.collect()
        return "false"

#########################PRISIJUNGIMO DALYKAI
def loginfnc(a, b):
    if a in root['users']:
        if sha256_crypt.verify(b, root['users'][a]['pwd']):
            flash("PRISIJUNGIMAS PAVYKO")
            return ("ok")
        else:
            flash("Neteisingi prisijungimo duomenys, bandykite dar kartą")
            gc.collect()
            return ("false")
    else:
        flash("Neteisingi prisijungimo duomenys, bandykite dar kartą")
        gc.collect()
        return ("false")

def handlelikedlist(product):
    product=str(product)
    if 'liked' not in session or session['liked']==[]:
        session['liked']=[product]
        return
    if product not in session['liked']:
        likedlist=session['liked']
        likedlist.extend([product])
        session['liked']=likedlist
        return
    else:
        likedlist=session['liked']
        if product in likedlist:
            likedlist.remove(product)
            session['liked']=likedlist
            return

def handlelikedlistzodb(producttoaddremove):
    if 'liked' not in session:
        session['liked']=[]
    if 'logged_in' not in session or session['logged_in']!=True:
        if producttoaddremove!=None:
            if producttoaddremove not in session['liked']:
                likedlist=session['liked']
                likedlist.extend(producttoaddremove)
                session['liked']=likedlist
                return
            else:
                likedlist=session['liked']
                likedlist.remove(producttoaddremove)
                session['liked']=likedlist
                return
        else:
            return

#    if session['logged_in']==True:                 GREICIAUSIAI DEL SITOS funkcijos KARTAIS IVIKSTA ZODB KLAIDA
#        username = jwt.decode(session['user'], secretkey, algorithm='HS256')['email']
#        userliked=root['users'][username]['liked']
#        liked=session['liked']
#        finalliked=list(set(liked+userliked))
#        if producttoaddremove!=None:
#            if producttoaddremove not in finalliked:
#                finalliked.extend(producttoaddremove)
#            else:
#                finalliked.remove(producttoaddremove)
#        session['liked']=finalliked
#        root['users'][username]['liked']=finalliked
#        root._p_changed=True
#        transaction.commit()
#        return





    username = jwt.decode(session['user'], secretkey, algorithm='HS256')['email']
    flash(root['users'][username]['getoffers'])
    flash(username)
    flash(session['user'])
    flash(session['logged_in'])
    flash(root['users'][username]['cart'])
#       root._p_changed=True
#        transaction.commit()
#        gc.collect()




def likedlistreturn():
    if 'liked' not in session or session['liked']==[]:
        return []
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    productlist=allproductsidlist()
    likedlist=session['liked']
    likedlist1=[]
    for a in likedlist:
        likedlist1.extend([[prekes[(int(a)-1)][productinfo('prname')], prekes[(int(a)-1)][productinfo('prprice')],
        prekes[(int(a)-1)][productinfo('prdiscount')], prekes[(int(a)-1)][0],prekes[(int(a)-1)][productinfo('prphoto1')]]])
    return likedlist1



def productcustomize(filelink):
    with open(filelink) as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    return(prekes)


def getlistforimageedit(directory, filelink, textlist, imgfromuser):
    #flash(textlist)
    csvlist=productcustomize(filelink)
    listas=[]
    texture=cv2.imread(directory+'engraved.jpg')
    for elementh in csvlist:
        edgelink=directory+"edge"+str(elementh[0])+".png"
        edge=cv2.imread(edgelink)
        filterlink=directory+"filter"+str(elementh[0])+".png"
        filterr=cv2.imread(filterlink)
        if elementh[3]=="text":
            listas.extend([[texture, edge, filterr, [int(elementh[10]),
            int(elementh[11])], elementh[3], [textlist[(int(elementh[0])-1)], "shop/fonts/"+elementh[7], elementh[8],elementh[9]]]])
        if elementh[3]=="img":
            if textlist[(int(elementh[0])-1)]=="":
                    cvimg = np.zeros((100, 100,3), np.uint8)
                    cvimg = cvimg+255
            else:
                imglink="shop/tmp/exampleuser/"+textlist[(int(elementh[0])-1)]
                cvimg=cv2.imread(imglink)
                r = 10.0 / cvimg.shape[1]
                dim = (10, int(cvimg.shape[0] * r))
                 #perform the actual resizing of the image and show it
                resized = cv2.resize(cvimg, dim, interpolation = cv2.INTER_AREA)
                cvimg=resized

            listas.extend([[texture, edge, filterr, [int(elementh[10]), int(elementh[11])], elementh[3], cvimg]])
    return listas

       # 0nr,1Pavadinimas,2Antraste pries inputa,3inputo tipas(text/img), 4max simbolių kiekis,
       # 5eilutes simboliu kiekis, 6eiliu sk, 7sriftas, 8srifto dydis, 9texto lygiavimas, 10propPLOTIS, 11propAUKSTIS

        ###0= texture, 1=edgesimg, 2=filterimg, 3=proportion, 4= contenttype, 5=content
                            ####if contenttype="img", tai content=paveiksliukas.jpg
                            ####if contenttype="textbox", tai content=[text, font, size, alignment]




#"shop/products/pvz1/product.csv"




def customizedimage():
    edge1=img=cv2.imread("shop/opencvtests/edge1.png")
    edge2=img=cv2.imread("shop/opencvtests/edge2.png")
    edge3=img=cv2.imread("shop/opencvtests/edge3.png")
    texture=cv2.imread("shop/opencvtests/boxengraved.jpg")
    putonimage=cv2.imread("shop/opencvtests/cicinas.jpg")
    img=cv2.imread("shop/opencvtests/box.jpg")
    font="shop/opencvtests/OpenSans-Bold.ttf"
    listas=[[texture, edge1, edge1, [1,3], "img", putonimage],[texture, edge2, edge2, [1,3], "img", putonimage],
            [texture, edge3, edge3, [1,3], "text", ["Jūsų tekstas čia\nArba čia\nVardas", font, 25, "right"]]]
    flash("costomizedimage", handleimgsandtext(listas, img))




def checkimagevalidity(filename):
    filename1=secure_filename(filename)
    if filename1.rsplit('.')[1] in ALLOWED_IMG_EXTENSIONS:
        validation=True
    else:
        validation=False
    return filename1, validation

def oneproductinputs(parameters):
    oneproduct=[]
    for a in parameters:
                postname="input"+str(a[0])
                if a[3]=='text':
                    oneproduct.extend([request.form[postname]])
                if a[3]=='img':
                    if postname not in request.files:
                        oneproduct.extend([request.form[postname]])
                    else:
                        file=request.files[postname]
                        checkedimg, validation=checkimagevalidity(file.filename)
                        if file.filename=="":
                            oneproduct.extend([""])
                        else:
                            if validation==False:
                                oneproduct.extend([""])
                                flash(file.filename+" netinkamas failo formatas")
                            else:
                                date=datetime.datetime.now()
                                dateedited=''.join(c for c in str(date) if c.isdigit())
                                filename1=checkedimg
                                filedirectory=directories['tmp']+session_name
                                if not os.path.exists(filedirectory):
                                    os.makedirs(filedirectory)
                                filedirectory+="/"+filename1
                                file.save(filedirectory)
                                oneproduct.extend([filename1])
    return [oneproduct]






session_name='exampleuser'#####LAIKINAS DALYKAS!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def getfieldvalue(inputtype, postname):##############################funkcija issaugo paveiksliuka ir grazina jo pavadinima arba texta
    if inputtype=='text':
        return request.form[postname]
    if inputtype=='img':
        if postname not in request.files:
            return request.form[postname]
        else:
            file=request.files[postname]
            checkedimg, validation=checkimagevalidity(file.filename)
            if file.filename=='':
                return ''
            else:
                if validation==False:
                    message=file.filename+" netinkamas failo formatas"
                    flash(message)
                    return ''
                else:
                    date=datetime.datetime.now()
                    #dateedited=''.join(c for c in str(date) if c.isdigit())
                    filedirectory=directories['tmp']+session_name

                    if not os.path.exists(filedirectory):
                        os.makedirs(filedirectory)

                    filedirectory=filedirectory+'/'+checkedimg
                    file.save(filedirectory)
                    return checkedimg

    with open("shop/categories.csv") as u:
        lastupdatedtmp=csv.reader(u)
        lastupdatedtmp = [r for r in kategorijos]
        tmpsessionnames=[]
        for a in lastupdatedtmp:
            tmpsessionnames.extend([a[0]])
    if session_name in tmpsessionnames:
        numberofname=tmpsessionnames.index(session_name)
        lastupdatedtmp[numberofname][1]=datetime.datetime.now()
    elif session_name not in tmpsessionnames:
        lastupdatedtmp.extend([[session_name, datetime.datetime.now()]])





def multipleproductsinputs(parameters, quantity):
    fullproductlist=[]
    for num in range(quantity):
        oneproductlist=[]
        count=0
        for a in parameters:
            requesttype=request.form['selection'+a[0]]
            if requesttype=='opt1':##################################Pasirinko klientas visiem taikyti ta pati
                if num!=0: #################################################Jei nebe pirmas produktas, tai kopijuoti parametra nuo pirmo
                    oneproductlist.extend([fullproductlist[0][count]])
                else:########################################################jei pirmas darom pilnai funkcija
                    oneproductlist.extend([getfieldvalue(a[3], 'input'+str(a[0]))])
            elif requesttype=='opt2':##############################Klientas pasirinko taikyti parametra pasirinktinai
                oneproductlist.extend([getfieldvalue(a[3], 'input'+str(a[0])+'num'+str(num))])
                #flash(oneproductlist)
            count+=1
            #flash('input'+str(a[0])+'num'+str(num))

        fullproductlist.extend([oneproductlist])
    return(fullproductlist)



def productconfigpostvalues(parameters, quantity):
    try:
        resultlist=[]
        if quantity==1:
            submitlist=oneproductinputs(parameters)
        elif quantity>1:
            submitlist=multipleproductsinputs(parameters, quantity)
        return submitlist


        #flash(submitlist)
    except Exception as e:
        flash(e)

def productconfigproductnumber(oldnum, newnum, chosen):
    try:
        newnum=int(newnum)
    except ValueError:
        return chosen
    diffrence=newnum-oldnum
    if diffrence==0:
        return chosen
    if diffrence>0:
        emptylist=['']
        emptylist=[emptylist*len(chosen[0])]*diffrence
        chosen=chosen+emptylist
        return chosen
    elif diffrence<0:
        chosen=chosen[0:diffrence]
        return chosen


def productinputinfo(prnum):
    filedest="shop/products/"+str(prnum)+".csv"
    with open(filedest) as u:
        prekes=csv.reader(u)
        next(prekes)
        inputsinfo=[r for r in prekes]
    #flash (inputsinfo)
    return inputsinfo

def handleaddtocart(inputinfo):
    for inp in inputinfo:
        inputvalue=request.form[inp[4]]
        flash(inputvalue)

def cartpricecounter(cartcont):
    with open("shop/products.csv") as u:
        prekes=csv.reader(u)
        next(prekes)
        prekes=[r for r in prekes]
    cartsum=0
    for pr in cartcont:
        prprice=float(prekes[int(pr['id'])-1][productinfo('prprice')])*int(pr['number'])
        cartsum+=prprice
    return(cartsum)



def omnivareturndict():
    locationsCSV="shop/omniva/locations.csv"
    with open(locationsCSV,) as u:
        locations=csv.reader(u, delimiter=';')
        next(locations)
        locationslist=[r for r in locations]
    addresslist=[]
    for a in locationslist:
        if a[3]=='LT':
            addresslist.extend([a[5]])
    return addresslist




################# UZSAKYMO VYKDYMO FUNKCIJOS ######################

#duomenų paėmimas iš formų
def getbuyerdata():
    if request.form['buyerType']=='fizinis':
        buyertype='fizinis'
        name=request.form['inputname']
        email=request.form['inputEmail']
        phone=request.form['inputNumber']
        organizationname='-'
        organizationaddress='-'
        organizationid='-'
        pvmid='-'
        deliverytype=request.form['DeliveryType']
        if deliverytype=='Omniva':
            omnivaaddress=request.form['omnivaaddress']
            address='-'
            city='-'
            zipcode='-'

        else:
            omnivaaddress='-'
            address=request.form['inputAddress']
            city=request.form['inputCity']
            zipcode=request.form['inputZip']

    elif request.form['buyerType']=='juridinis':
        buyertype='juridinis'
        name=request.form['inputcontactnameJur']
        email=request.form['inputEmailJur']
        phone=request.form['inputNumberJur']
        organizationname=request.form['organizationname']
        organizationaddress=request.form['registrationaddress']
        organizationid=request.form['organizationid']
        pvmid=request.form['pwmid']
        deliverytype=request.form['DeliveryTypeJur']

        if deliverytype=='Omniva':
            omnivaaddress=request.form['omnivaaddressJur']
            address='-'
            city='-'
            zipcode='-'

        else:
            omnivaaddress='-'
            address=request.form['inputAddressJur']
            city=request.form['inputCityJur']
            zipcode=request.form['inputZipJur']

    return {'buyer type':buyertype, 'name':name, 'email':email, 'phone':phone, 'organization name':organizationname,
    'organization address':organizationaddress, 'organization id':organizationid, 'pvm id':pvmid,
    'delivery type':deliverytype, 'omniva address':omnivaaddress,'address':address, 'city':city, 'zip code':zipcode}



def setorder(buyerinfo, order_data, orderstatus):
    orderlist_file=orderlistfileid

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    client=gspread.authorize(credentials)
    date=datetime.datetime.now()
    sheet=client.open_by_key(orderlist_file)
    sheet=sheet.worksheet('orders')
    orderidlist=sheet.col_values(1)
    if len(str(date.day))==1:
        q='0'+str(date.day)
    else:
        q=str(date.day)
    id=q+str(random.randint(1,99))+str(len(orderidlist))
    #order_data=str(order_data)
    ordersheetname=str(date.year)+str(date.month)+str(date.day)+str(id)+str(buyerinfo['name'])+str(random.randint(1,101))


##################save txt file
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    file1 = drive.CreateFile({'title': ordersheetname+'.txt',
                            'parents': [{
                            'id': EshopOrderdatatxtfilesID
                            }]
                            })  # Create GoogleDriveFile instance with title 'Hello.txt'.
    file1.SetContentString(order_data) # Set content of the file from given string.
    file1.Upload()
    datatxtfileid=file1['id']


#################

    row=[str(id), str(date), orderstatus, buyerinfo['buyer type'], buyerinfo['name'], 'banko acc', 'suma', buyerinfo['email'],
    buyerinfo['phone'], buyerinfo['organization name'], buyerinfo['organization address'], buyerinfo['organization id'],
    buyerinfo['pvm id'], buyerinfo['delivery type'], buyerinfo['omniva address'], buyerinfo['address'], buyerinfo['city'],
    buyerinfo['zip code'], '', '', '', '', ordersheetname, datatxtfileid]
    sheet.append_row(row)
    return id


def getpricelistfromuserdict(userdict):
    orderlist=[]
    for a in userdict:
        productinfo=getproductinfo(a['productid'])
        orderlist.append({'price':int(productinfo['price']), 'discount':int(productinfo['discount']), 'productname': productinfo['name'],'productid':a['productid'] ,'productnumber':len(a['productlist'])})
    return orderlist



def countcartprice(deliverytype, pricelist):
    price=0
    for a in pricelist:
        price+=int(a['price'])*int(a['productnumber'])
    if deliverytype=='Omniva':
        price+=deliveryprices['ltu']['Omniva']
    elif deliverytype=='LPregistered':
        price+=deliveryprices['ltu']['LPregistered']
    return price



alphabet='abcdefghijklmnroprstuv'


def getproductnumberfromuserdict(userdict):
    counter=0
    userdict=json.loads(userdict)
    for a in userdict:
        for e in a['productlist']:
            counter+=1
    return counter

def setunpaidorderincsvline(buyerinfo, order_data, fullprice, orderstatus):
    numberofproducts=getproductnumberfromuserdict(order_data)
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name(credentialsfile, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    currentToollist = drive.CreateFile({'id': unpaidordersjsonID})
    currentToollist.GetContentFile(serverfolder+'/tmp/unpaidorders.csv')
    with open(serverfolder+'/tmp/unpaidorders.csv', 'r') as u:
        jsonorderlist=json.loads(u.read())


    date=datetime.datetime.now()

    q=alphabet[random.randint(0,21)].upper()+ alphabet[date.month].upper() +str(date.year)[-1]

    if len(str(date.day))==1:
        q=q+'0'+str(date.day)+str(date.minute)
    else:
        q=q+str(date.day)+str(date.minute)
    id=q
    #order_data=str(order_data)
    ordersheetname=str(date.year)+str(date.month)+str(date.day)+str(id)+str(buyerinfo['name'])+str(random.randint(1,101))


##################save txt file
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    file1 = drive.CreateFile({'title': ordersheetname+'.txt',
                            'parents': [{
                            'id': unpaidorderGoogleDrivefileID
                            }]
                            })  # Create GoogleDriveFile instance with title 'Hello.txt'.
    file1.SetContentString(order_data) # Set content of the file from given string.
    file1.Upload()
    datatxtfileid=file1['id']

#################

    row=[str(id), str(date), orderstatus, buyerinfo['buyer type'], buyerinfo['name'], 'banko acc', fullprice, buyerinfo['email'],
    buyerinfo['phone'], buyerinfo['organization name'], buyerinfo['organization address'], buyerinfo['organization id'],
    buyerinfo['pvm id'], buyerinfo['delivery type'], buyerinfo['omniva address'], buyerinfo['address'], buyerinfo['city'],
    buyerinfo['zip code'], '', '', '', '', ordersheetname, datatxtfileid, str(numberofproducts)]
    jsonorderlist.append(row)
    jsonorderlistdumped=json.dumps(jsonorderlist, indent=4)
    file1 = drive.CreateFile({'id': unpaidordersjsonID})
    file1.SetContentString(jsonorderlistdumped)
    file1.Upload()
    return jsonorderlist[-1]


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

def simpledeliverycounter():
    weekdays={'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6,'Sunday':7}
    #date=datetime.datetime.now()
    weekday=weekdays[datetime.datetime.today().strftime('%A')]
    day=datetime.datetime.today().day
    month=datetime.datetime.today().month
    year=day=datetime.datetime.today().year
    if weekday<6:
        sendingday=datetime.datetime.today()+datetime.timedelta(7-int(weekday)+2)
        plannedday=str(sendingday.year)+'/'+str(sendingday.month)+'/'+str(sendingday.day)
    else:
        sendingday=datetime.datetime.today()+datetime.timedelta(7)
        plannedday=str(sendingday.year)+'/'+str(sendingday.month)+'/'+str(sendingday.day)
    return(str(plannedday))




