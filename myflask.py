import os
from flask import Flask, render_template, flash, request, url_for, redirect, session, jsonify, send_from_directory
from shopfunctions import setunpaidorderincsvline, stripe_keys, setorder, getbuyerdata, omnivareturndict, cartpricecounter, cartproductsinfo, handleaddtocart, productinputinfo, registerfnc, loginfnc, searchfnc, csvcategories, getproductinfo, suggestproducts,suggestproducts, suggestsimilarproducts, handlelikedlist, likedlistreturn, handlelikedlistzodb, productcustomize,customizedimage,productconfigpostvalues, getlistforimageedit, productconfigproductnumber, deliveryprices, getpricelistfromuserdict, countcartprice, getFileDotJson, simpledeliverycounter
import jwt
import datetime
import json
import stripe
from shopbackendfunctions import prgetorderlist, getorderexelrowsandsvgs, getuserdicts, makesvg, getordersvgs, setSvgsFinished, checkandaddpaymentsfromsms, manageSMSpaymentdata, getfilejsonfromdrive, getordernumber, addordertoordersheet, getordersvgs1, getorderdatabyid, storeinvoiceidanddate
from cncworkshop import getdrivefile, removetools, f360toollibrries, toolinputdata, addtoolfromlibrary
from flask_weasyprint import HTML, render_pdf
from flask_mail import Mail, Message
from cellphoneoperator import setpayment
#from paypal import PayPalInterface
import paypalrestsdk
from werkzeug.utils import secure_filename
from flask_basicauth import BasicAuth




###IMG KALIBRAVIMUI
from calibrateengravings import handlecalibration

SwedbankPaymentsID=os.environ.get("googledisc_payments/SwedbankPaymentsTXT")##### GOOGLE DISC FILE

app= Flask(__name__)
shopcontacts={'Facebook':'https://www.facebook.com/kaziukas24.lt'}
webdata={'phone':os.environ.get('seller_phone'),'email':os.environ.get("seller_mail"), 'copyright':['IgnasMakes','www.ignasmakes.com'],'shopname': os.environ.get('shopname'),'contacts':shopcontacts}
seller={'name':os.environ.get("seller_name"), 'sellercode':os.environ.get("seler_idcode"), 'selleremail':os.environ.get("seller_mail"), 'indveikloskodas':os.environ.get('seller_businessidcode'),'sellerphone':os.environ.get('seller_phone'), 'bankacc':os.environ.get('seller_bankacc'), 'address':os.environ.get('seller_address')}

app.config.update(
	DEBUG=False, ################################NORINT MATYT KLAIDAS TRUE
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.flockmail.com',#####EX param= 'smtp.gmail.com'
	MAIL_PORT=587,#####EX param= 465
	#MAIL_USE_SSL=True, ##google parametras
	#MAIL_USE_TLS = True, ### Flockmail parametras
	MAIL_USERNAME = os.environ.get("mail_login"),
	MAIL_PASSWORD = os.environ.get("mail_pwd"),
	tmpfolder = "/home/Likvaras/shop/tmp",
	)
	###naudojant gmail reikia reikia nustatyti: 1. Allow less secure apps: ON. (https://myaccount.google.com/lesssecureapps)
mail = Mail(app)

secretkey=os.environ.get("jwt_secretcode")   ##naudojama su jwt encode
app.secret_key = os.environ.get("flask_appsecretcode")
stripe.api_key = stripe_keys['secret_key']


app.PERMANENT_SESSION_LIFETIME = False
app.config['BASIC_AUTH_USERNAME'] = os.environ.get("productionpageslogin")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('productionpagespwd')

basic_auth = BasicAuth(app)



###############funkcija kuri vyksta gavus requesta is telefono BETA VERSIJA
@app.route('/addorder/', methods=['GET', 'POST'])
def addorder():
    orderid=request.form['ordertoaddid']
    ordersum=request.form['payedmoney']
    if addordertoordersheet([[orderid, ordersum]])=='OK':
        flash('Successfully added !')
        return redirect(url_for('production'))

 


@app.route('/payment/', methods=['POST'])
def payment():
    payment = paypalrestsdk.Payment({
    "intent": "sale",
    "payer": {
        "payment_method": "paypal"},
    "redirect_urls": {
        "return_url": "http://localhost:3000/payment/execute",
        "cancel_url": "http://localhost:3000/"},
    "transactions": [{
        "item_list": {
            "items": [{
                "name": "item",
                "sku": "item",
                "price": "5.00",
                "currency": "USD",
                "quantity": 1}]},
        "amount": {
            "total": "5.00",
            "currency": "USD"},
        "description": "This is the payment transaction description."}]})
    if payment.create():
        print("Payment created successfully")
    else:
        flash(str(payment.error))

    return jsonify({'paymentID':payment.id})







@app.route('/')
def index():
    suggestion=suggestproducts()
    return render_template('home.html', webdata=webdata, pagetitle=webdata['shopname'], suggestion=suggestion)

@app.route('/taisykles/')
def rules():
        return render_template('rules.html', webdata=webdata, pagetitle="Taisyklės - "+webdata['shopname'])

@app.route('/katalogas/')
def catalogue():
    return render_template('catalogue.html', webdata=webdata, pagetitle="Katalogas - "+webdata['shopname'], listas=csvcategories())


@app.route('/apie/')
def aboutus():
        return render_template('aboutus.html', webdata=webdata, pagetitle="Apie mus - "+webdata['shopname'])

@app.route('/kontaktai/')
def contacts():
    return render_template('contacts.html', webdata=webdata, pagetitle="Kontaktai - "+webdata['shopname'], message="laabas")


@app.route('/prisijungti/', methods=['GET', 'POST'])#####Beta
def login():
    if request.method == "POST":
        if loginfnc(request.form["email"], request.form["pwd"])=="ok":
            session['logged_in']=True
            session['user'] = jwt.encode({"email":request.form["email"]}, secretkey, algorithm='HS256')
            return redirect(url_for('index'))
    return render_template('login.html', webdata=webdata, pagetitle="Prisijungti - "+webdata['shopname'])

@app.route('/logout/')####Beta
def logout():
    session.pop('logged_in')
    session.pop('user')
    return redirect(url_for('index'))

@app.route('/paskyra/')####Beta
def userpage():
    return render_template('userpage.html', webdata=webdata, pagetitle="Paskyra - "+webdata['shopname'])

@app.route('/patiko/')
def liked():
    return render_template('likedproducts.html', webdata=webdata, pagetitle="Įsiminti produktai - "+webdata['shopname'])

@app.route('/registruotis/', methods=['GET', 'POST'])
def register():
    try:
        if request.method == "POST":
            email=request.form["email"]
            if registerfnc(request.form["pwd"], request.form["pwdconfirm"], email, str(request.values.get("notifications")))=="ok":
                session['logged_in']=True
                session['user'] = encoded_jwt = jwt.encode({"email":email}, secretkey, algorithm='HS256')
                return redirect(url_for('index'))
    except Exception as e:
        flash(e)

    return render_template('register.html', pagetitle="Registracija - "+webdata['shopname'])

@app.route('/isimintos-prekes/', methods=['GET', 'POST'])
def likedproducts():
    handlelikedlistzodb(None)
    if request.method== "POST":
        handlelikedlistzodb(request.form["remove"])
    likedlist=likedlistreturn()
    return render_template('likedproducts.html', webdata=webdata, pagetitle="Įsiminti produktai - "+webdata['shopname'], likedlist=likedlist)

@app.route('/krepselis/')
def cart():
    if 'productsidincart' in request.cookies:
        productlist=eval(request.cookies.get('productsidincart'))
        #flash(productlist)
        cartinfo=cartproductsinfo(productlist)
    else:
        cartinfo=[]
    #flash(cartinfo)
    return render_template('cart.html', webdata=webdata, pagetitle="Krepšelis - "+webdata['shopname'], cartinfo=cartinfo, planeddelivery=simpledeliverycounter())


@app.route('/shipping/', methods=['GET', 'POST'])
def shipping():
    try:
        if request.method== "POST":
            cartcontent=eval(request.form.getlist("cartdata")[0])
            price=cartpricecounter(cartcontent)
        else:
            return redirect(url_for('cart'))
    except Exception as e:
        flash('Atsiprašome už nesklandumus')
        redirect(url_for('cart'))
    return render_template('shipping.html', webdata=webdata, deliveryprices=deliveryprices, pagetitle="Užsakymas - "+webdata['shopname'], price=price, omnivalist=omnivareturndict())

@app.route('/uzsakymovykdymas/', methods=['GET', 'POST'])
def checkoutsubmit():
    try:
        if request.method== "POST":
            buyerdata=getbuyerdata()
            order_data = request.form.getlist('storagedict')[0]
            return(setorder(buyerdata, order_data))
        else:
            return redirect(url_for('cart'))
    except Exception as e:
        return(e)
    return redirect(url_for('cart'))


@app.route('/apmokejimas/', methods=['GET', 'POST'])
def checkoutpage():
    try:
        if request.method== "POST":
            buyerdata=getbuyerdata()
            cartdata=getpricelistfromuserdict(json.loads(request.form.getlist('storagedict')[0]))
        else:
            return redirect(url_for('cart'))
    except Exception as e:
        return(e)
    return render_template('checkout/checkout.html', webdata=webdata, pubkey=stripe_keys['publishable_key'], pagetitle="Apmokejimas - "+webdata['shopname'], cartdata=cartdata, buyerdatadumped=json.dumps(buyerdata), buyerdata=buyerdata, deliveryprices=deliveryprices, cartprice=countcartprice(buyerdata['delivery type'], cartdata), planeddelivery=simpledeliverycounter())



@app.route('/invoice/')###testinis linkas
def invoice():
    sourceHtml = render_template('invoice/Invoice.html', seller=seller, cartdata={'orderid':'Užsakymas123456', 'cartprice':12345, 'deliverytype':'omniva', 'deliveryprice':69, 'cartlist':[{'name':'Puodelio padekliukas', 'id':'5', 'price':699, 'number':3, 'fullprice':210}]} )
    return render_pdf(HTML(string=sourceHtml))


@app.route('/banktransaction', methods=['POST'])
def banktransaction():
    #try:
        userdict=request.form.getlist('storagedict')[0]
        cartdata=getpricelistfromuserdict(json.loads(userdict))
        fullprice=0
        #flash(cartdata)
        for a in cartdata:
            fullprice+=a['price']*a['productnumber']
        buyerdata=json.loads(request.form.getlist('buyerdata')[0])
        fullprice+=deliveryprices['ltu'][buyerdata['delivery type']]
        if fullprice==int(request.form.getlist('cartprice')[0]):
            ordernumber=setunpaidorderincsvline(buyerdata, userdict, fullprice, 'unpayed')###############issaugomas uzsakymas
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
            cartdata={'orderid':ordernumber[0], 'cartprice':int(fullprice), 'deliverytype':buyerdata['delivery type'], 'deliveryprice':deliveryprices['ltu'][buyerdata['delivery type']], 'cartlist':cartlist}
            invoicehtml = render_template('invoice/Invoice.html', seller=seller, cartdata=cartdata, buyerdata=buyerdata, invoicetext='Išankstinė sąskaita faktūra', invoicetext1='' )


            h3='Sveiki, '+buyerdata['name']+','
            emailhtml=render_template('email templates/order.html', fullprice=fullprice,h3=h3, shopname=webdata['shopname'], seller=seller, ordernumber=ordernumber[0], deliverydate=simpledeliverycounter())
            msg = Message(webdata['shopname']+" Užsakymas priimtas", sender="info@kaziukas24.lt", recipients=[buyerdata['email']])
            msg.html=emailhtml

            pdf = HTML(string=invoicehtml).write_pdf('shop/tmp/preinvoice.pdf')

            with app.open_resource("tmp/preinvoice.pdf") as pdf:
                msg.attach("saskaita.pdf", "application/pdf", pdf.read())
            mail.send(msg)
            preinvoicerendered=render_pdf(HTML(string=invoicehtml))
            invoicetext='Išankstinė sąskaita faktūra'
            return render_template('checkout/completed.html', webdata=webdata, invoicetext=invoicetext, pdf=invoicehtml, paytype='invoice', orderstatus='completed', seller=seller, cartdata=cartdata, buyerdata=buyerdata )


        return render_template('checkout/completed.html', paytype='invoice', orderstatus='not')

@app.route('/saskaita', methods=['POST'])
def saskaita():
    pdf=request.form.getlist('pdf')[0]
    return render_pdf(HTML(string=pdf))


@app.route('/charge', methods=['POST'])
def charge():
    try:
        amount=request.json['amount']
        customer = stripe.Customer.create(
            email='sample@customer.com',
            source=request.json['token']
        )
        stripe.Charge.create(
            customer=customer.id,
            amount=request.json['amount'],
            currency='usd',
            description=request.json['description']
        )
        return redirect(url_for('cart'))
    except stripe.error.StripeError:
        return jsonify({'status': 'error'}), 500



@app.route('/paieska/', methods=['GET', 'POST'])
def paieska():
    try:
        #productlist=[]
        if request.method == "POST":
            page=int(request.form["page"])
            keywords=request.form["prkeywords"]
            category=request.form.getlist("prcategory")
            material=request.form.getlist("prmaterial")
            pricebegins=request.form["kainanuo"]
            priceends=request.form["kainaiki"]
            interestclasses=request.form["printerestsclass"]
            similarproducts=request.form["prsimilarproducts"]
            searchresults=searchfnc(page, keywords, category, material, pricebegins, priceends, interestclasses, similarproducts)
        else:
            page=1
            keywords=""
            category=[]
            material=[]
            pricebegins=""
            priceends=""
            interestclasses=''
            similarproducts=''
            searchresults=searchfnc(page, "", [], [], "", "", "", "")

        return render_template('search.html', webdata=webdata, pagetitle="Produktai - ", listas=csvcategories(), searchresults=searchresults, keywords=keywords, category=category,
        material=material, pricebegins=pricebegins, priceends=priceends, page=page, paginationlen=int(searchresults['pagination']), interestclasses=interestclasses, similarproducts=similarproducts)
    except Exception as e:
        flash(e)
        return redirect(url_for('paieska'))



@app.route('/preke/<productid>/', methods=['GET', 'POST'])
def preke(productid):
    modifyorcreatenew=None
    #inputinfo=productinputinfo(productid)
    suggestion=suggestsimilarproducts(productid)
    productinfo=getproductinfo(productid)
    if productinfo==None:
        #flash("Nurodytos prekės nėra")
        return redirect(url_for('paieska'))

    if request.method == "POST":
        if request.form["formmission"]=="rememberproduct":
            if request.form["add"]!="":
                handlelikedlist(request.form["add"])

        elif request.form["formmission"]=="buy":
            handleaddtocart(inputinfo)

        elif request.form["formmission"]=="changeproductincart":
            modifyorcreatenew=request.form['productnumincart']


    return render_template('productpage.html', webdata=webdata, imageid='0B5_mrYtiuzIjMjRxdXl2dEtoQlE', pagetitle=(str(productinfo["name"])+" -"+webdata['shopname']), productinfo=productinfo, suggestion=suggestion, productid=productid, modifyorcreatenew=modifyorcreatenew)



@app.route('/configure/<productid>/', methods=['GET', 'POST'])
def configure(productid):
    productinfo=getproductinfo(productid)
    if productinfo['type']=='basic':
        return redirect(url_for('preke', productid=str(productid)))
    modifyorcreatenew=None
    inputinfo=productinputinfo(productid)
    suggestion=suggestsimilarproducts(productid)
    if productinfo==None:
        flash("Nurodytos prekės nėra")
        return redirect(url_for('paieska'))

    if request.method == "POST":
        if request.form["formmission"]=="rememberproduct":
            if request.form["add"]!="":
                handlelikedlistzodb(request.form["add"])

        elif request.form["formmission"]=="buy":
            handleaddtocart(inputinfo)

        elif request.form["formmission"]=="changeproductincart":
            modifyorcreatenew=request.form['productnumincart']


    return render_template('customizeproduct.html', webdata=webdata, inputinfo=inputinfo, pagetitle=(str(productinfo["name"])+" -"+webdata['shopname']), productinfo=productinfo, suggestion=suggestion, productid=productid, modifyorcreatenew=modifyorcreatenew)



@app.route('/configure/<productid>/2d', methods=['GET', 'POST'])
def configure2d(productid):
    productinfo=getproductinfo(productid)
    if productinfo['type']=='basic':
        return redirect(url_for('preke', productid=str(productid)))
    modifyorcreatenew=None
    inputinfo=productinputinfo(productid)
    suggestion=suggestsimilarproducts(productid)
    if productinfo==None:
        flash("Nurodytos prekės nėra")
        return redirect(url_for('paieska'))

    if request.method == "POST":
        if request.form["formmission"]=="rememberproduct":
            if request.form["add"]!="":
                handlelikedlistzodb(request.form["add"])

        elif request.form["formmission"]=="buy":
            handleaddtocart(inputinfo)

        elif request.form["formmission"]=="changeproductincart":
            modifyorcreatenew=request.form['productnumincart']


    return render_template('product/2d editor/main.html', webdata=webdata, inputinfo=inputinfo, pagetitle=(str(productinfo["name"])+" -"+webdata['shopname']), productinfo=productinfo, suggestion=suggestion, productid=productid, modifyorcreatenew=modifyorcreatenew)



@app.route('/customizeproduct/<productidd>/', methods=['GET', 'POST'])
def productconfig(productidd):
    parameters=productcustomize("shop/products/"+productidd+"/product.csv")
    #customizedimage()
    if request.method == "POST":
        if request.form["action"]=="config":
            quantity=int(request.form["quantity"])
            flash(quantity)
            return render_template('customizeproduct.html', parameters=parameters, productnumber=quantity, productid=productidd, chosen=None)
        if request.form["action"]=="modify":
            try:
                quantity=int(request.form["quantity"])
                newquantity=request.form["newquantity"]
                chosen=productconfigpostvalues(parameters, quantity)

                chosen=productconfigproductnumber(quantity, newquantity, chosen)
                flash(chosen)
                return render_template('customizeproduct.html', parameters=parameters, productnumber=len(chosen), productid=productidd, chosen=chosen)
            except Exception as e:
                flash(e)
                return render_template('customizeproduct.html', parameters=parameters, productnumber=1, productid=productidd, chosen=None)
    return render_template('customizeproduct.html', webdata=webdata, parameters=parameters, productnumber=1, productid=productidd, chosen=None)


@app.route('/tmpfiles/<filename>')
def return_tmp_file(filename):
	try:
		return send_from_directory('tmp', filename, cache_timeout=0)
	except Exception as e:
		return flash(e)



####################################FUNKCIJOS GAMYBAI

@app.route('/production/', methods=['GET', 'POST'])
@basic_auth.required
def production():
    try:
        orderlist=prgetorderlist()
        if request.method=='POST':
            action=request.form["action"]
            if action=='showall':
                swedbankMessages=getFileDotJson(SwedbankPaymentsID)
                return render_template('manufacture/ProductionMain.html', orderstoshow='all', orderlist=orderlist, swedbankMessage=swedbankMessages)
            elif action=='only on process':
                swedbankMessages=getFileDotJson(SwedbankPaymentsID)
                return render_template('manufacture/ProductionMain.html', orderstoshow=action, orderlist=orderlist, swedbankMessages=swedbankMessages)

            elif action=='CreateSvg':######################################################PAGAMINA SVG
                makesvg(getorderexelrowsandsvgs(json.loads(request.form["POSTorderlist"])))
                swedbankMessages=getFileDotJson(SwedbankPaymentsID)
                return render_template('manufacture/ProductionMain.html', orderstoshow='only on process', orderlist=prgetorderlist(), swedbankMessages=swedbankMessages)

        swedbankMessages=getFileDotJson(SwedbankPaymentsID)
        swedbankMessages=swedbankMessages
        return render_template('manufacture/ProductionMain.html', webdata=webdata, orderstoshow='only on process',orderlist=orderlist, swedbankMessages=swedbankMessages)
    except Exception as e:
        return str(e)


@app.route('/production/organizemanufactureallpayed/', methods=['GET', 'POST'])
@basic_auth.required
def organizesvg():
    if request.method=='POST':
        orderlist=json.loads(request.form["POSTorderlist"])
        return render_template('manufacture/organizemanufacture.html', webdata=webdata, orderlist=makesvg(getorderexelrowsandsvgs(orderlist)))



@app.route('/production/order/<orderid>/<openmode>/', methods=['GET', 'POST'])
@basic_auth.required
def order(orderid, openmode):
        openmode=str(openmode)
        orderinfo=getorderexelrowsandsvgs([orderid])

        if request.method=='POST':
            action=request.form["action"]
            if action=='SetSvgsFinished':
                finishedsvgslist=json.loads(request.form["POSTproductlist"])
                finishedsvgslist=setSvgsFinished(getorderexelrowsandsvgs([orderid]), finishedsvgslist)
                if openmode=='fast':
                    ordersvgslistfile=getordersvgs1(orderinfo)
                if openmode=='slow':
                    ordersvgslistfile=getordersvgs(orderinfo)
                return render_template('manufacture/order.html', orderid=orderid, orderinfo=orderinfo,ordercontent=ordersvgslistfile, finishedsvgslist=finishedsvgslist)
        if openmode=='fast':
            ordersvgslistfile=getordersvgs1(orderinfo)
        if openmode=='slow':
            ordersvgslistfile=getordersvgs(orderinfo)
        return render_template('manufacture/order.html', orderid=orderid, orderinfo=orderinfo,ordercontent=ordersvgslistfile, finishedsvgslist=' ',openmode=openmode)



@app.route('/production/invoice/<orderid>/', methods=['GET', 'POST'])
@basic_auth.required
def orderinvoice(orderid):
    orderinfo=getorderexelrowsandsvgs([orderid])
    date=datetime.date.today()
    userdict=getfilejsonfromdrive(orderinfo[0][23])
    cartdata=getpricelistfromuserdict(userdict)
    fullprice=orderinfo[0][19]
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
    cartdata={'orderid':orderinfo[0][0], 'cartprice':int(fullprice), 'deliverytype':orderinfo[0][13], 'deliveryprice':deliveryprices['ltu'][orderinfo[0][13]], 'cartlist':cartlist}
    invoicetext1='Serija IJ Nr.'+str(getordernumber(orderinfo[0][0]))
    invoicetext='Sąskaita faktūra'

    if request.method=='POST':
        invoicetext1=request.form["fakturosnr"]
        date=request.form["data"]
        buyerdata={'buyer type':orderinfo[0][3], 'name':orderinfo[0][4], 'email':orderinfo[0][7], 'phone':orderinfo[0][8], 'delivery type':orderinfo[0][13], 'omniva address':orderinfo[0][14], 'address':orderinfo[0][15], 'organization name':orderinfo[0][9], 'organization id':orderinfo[0][11], 'pvm id':orderinfo[0][12], 'organization address':orderinfo[0][10]}
        invoicehtml = render_template('invoice/Invoice.html', seller=seller, cartdata=cartdata, buyerdata=buyerdata, invoicetext=invoicetext, invoicetext1=invoicetext1, date=date)
        h3='Sveiki, '+buyerdata['name']+','
        emailhtml=render_template('email templates/paymentaccepted.html', invoiceid=invoicetext1, fullprice=fullprice,h3=h3, shopname=webdata['shopname'], seller=seller, ordernumber=orderinfo[0][0])
        msg = Message(webdata['shopname']+" apmokėjimo patvirtinimas", sender="info@kaziukas24.lt", recipients=[buyerdata['email']])
        msg.html=emailhtml
        pdf = HTML(string=invoicehtml).write_pdf('shop/tmp/preinvoice.pdf')
        with app.open_resource("tmp/preinvoice.pdf") as pdf:
            msg.attach("saskaita.pdf", "application/pdf", pdf.read())
            mail.send(msg)
        storeinvoiceidanddate(orderid, str(date), invoicetext1)
        flash('INVOICE SENT SUCCESFULLY !')

    return render_template('manufacture/orderinvoice.html',invoicetext=invoicetext, invoicetext1=invoicetext1, buyerdata=orderinfo[0],orderid=orderid, seller=seller, date=date, cartdata=cartdata)



ALLOWED_EXTENSIONS = set(['jpg', 'svg'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#####Beta vesija gamybai lazeriu
@app.route('/calibrateengravings/', methods=['GET', 'POST'])
@basic_auth.required
def calibrateengravings():
    if request.method == "POST":
        if request.files:
            engraveimage = request.files['engraveimage']
            workimage = request.files['workimage']
        else:
            return 'No file uploaded'

        if workimage and allowed_file(workimage.filename) and engraveimage and allowed_file(engraveimage.filename):
            engraveimage.save(os.path.join(app.config["tmpfolder"], 'engravetest.jpg'))
            workimage.save(os.path.join(app.config["tmpfolder"], 'workimage.svg'))
         #   engraveimage.save('work.svg')
            return handlecalibration()
    return render_template('ignasmakes/calibrateengravings.html', pagetitle='Laser test')

###########Kolkas neveikia
@app.route('/productphotogenerator/', methods=['GET', 'POST'])
@basic_auth.required
def productphotogenerator():
    img="./shop/productphotogenerator/image.png"
    putonimage="./shop/productphotogenerator/mydesign.jpg"
    mask="./shop/productphotogenerator/edges.jpg"
    ratio=[2,3]
    texture="./shop/productphotogenerator/engraved.png"
    flt="./shop/productphotogenerator/filter.jpg"
    CreateImage(img, putonimage, mask, ratio, texture, flt)
    return 'productgenerator'
#############################################################################




#######-------------------------CNC SHOP ZONE-----------------
shopurl='YourWorkShopName'
credentialsfile= 'shop/creds.json'
serverfolder= os.environ.get("directories_eshopdir")
currentToollistfileid='17-ex6va6URfdophZmEZ_krXDF7QgaaC0'
wornouttoolsfileid='1T9p3T0ec_7fBsujYXJ528pOy1TZn8ah8'


@app.route(str('/'+shopurl+'/'))
@basic_auth.required
def totalcustoms():
    return render_template('/cncworkshop/tools.html', content=currenttoolslist(), shopurl=shopurl)

@app.route('/'+shopurl+'/'+'tools/', methods=['GET', 'POST'])
@basic_auth.required
def tools():
    message= 'No message'
    if request.method=='POST':
        if request.form.get('mission')=='wornout':
            message='wornout'
            wornoutlist=[]
            currenttools=getdrivefile(currentToollistfileid)
            for a in currenttools['data']:
                if 'checked' in request.form.getlist(str(a)):
                    wornoutlist.append(a)
            newcurrentlist=removetools(wornoutlist, currenttools)

        elif request.form.get('mission')=='addfromlib':
            addtoolfromlibrary()
            newcurrentlist=getdrivefile(currentToollistfileid)

        elif request.form.get('mission')=='addf3dlib':
            message='addf3dlib'
            newcurrentlist=getdrivefile(currentToollistfileid)


    else:
        newcurrentlist=getdrivefile(currentToollistfileid)
    return render_template('/cncworkshop/tools.html', message=message, currenttools=newcurrentlist, shopurl=shopurl, worntools=getdrivefile(wornouttoolsfileid), libraries=f360toollibrries, toolinputdata=toolinputdata)
########### --------------END CNC SHOP ZONE-----------------


@app.errorhandler(404)
@app.errorhandler(500)
def page_not_found(e):
    suggestion=suggestproducts()
    flash('Klaida, puslapis nerastas')
    return render_template('home.html', webdata=webdata, pagetitle="ShopName", suggestion=suggestion)


if __name__ == '__main__':
	app.run()