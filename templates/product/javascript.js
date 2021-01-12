
<script>




function setdictionary(){////////////////////////////funkcija kuri paima trecia preke is cart ir ja atidaro
    dict=JSON.parse(localStorage.getItem("cart"))
    ShoppingDict=dict[3]
    refreshProductNumber()
    selectProductNum()
};

function getcartdata(){
    var cart=localStorage.getItem("cart")
    cart=JSON.parse(cart);
    if(cart==null){cart=[]};
    return cart;
    }

function updatecart(){
    var cart=getcartdata();
    if(document.getElementById('addtocart').value=='buy'){
            var newnumber=cart.length;
    };
    cart[newnumber]=ShoppingDict
    localStorage.setItem("cart", JSON.stringify(cart))
    return cart
    }

function addtocart(){
    document.getElementById('addtocart').disabled=true
    var d = new Date();
    d.setTime(d.getTime() + (3600*24*60*60*1000));////KUKIS LAIKOMAS 3600 DIENAS
    var expires = ";expires="+ d.toUTCString();

    cart=updatecart();
    productidlist=[];
    for(p=0; p<cart.length; p++){
        productidlist[p]=cart[p]['productid'];
        console.log(productidlist)
    };
    productidlist = JSON.stringify(productidlist);
    document.cookie = "productsidincart="+productidlist+expires+ "; path=/krepselis/";
    window.location.href = '/krepselis/';
    /////////////////post('/krepselis/', {'productlist': productidlist});
};



function checkInp(x)///////////////////////FUNKCIJA PATIKRINA AR SKAICIUS AR TEKSTAS
{
  if (isNaN(x))
  {
    alert("Įveskite prekių skaičių skaitmenimis");
    return false;
  }
};

var ShoppingDict={
    'productid':document.getElementById('productid').value,
    'productlist':[],
    'imglist':{}
};





var inputlist={{inputinfo|safe}};
var featurenumber=inputlist.length  //////////Pasako kiek parinkimu ira produkte. pvz antraste, paveikslelis, tekstas =3

function selectproductmenuShowHide(number){
    for(i=0; i<number; i++){
        document.getElementById('btn'+i).hidden = false;
    };
    for(i=number; i<200; i++){
        document.getElementById('btn'+i).hidden = true;
    };
};


function showproductlist()///////////Funkcija kuria naudoja visu pasirinktu produktu mygtukas, kuris grazina moduli su sios funkcijos turiniu
    {
    showproductsonfiguration=''
    for(i=0; i<ShoppingDict['productlist'].length; i++){
        showproductsonfiguration+='<b>'+(i+1)+':</b> '

        for(index=0; index<inputlist.length; index++) {
        var linevalue=''
        if(inputlist[index][2]=='text'){
            if(ShoppingDict['productlist'][i][inputlist[index][1]]==''){linevalue='<font color="red">neįkeltas tekstas!</font>'}
            else{linevalue=ShoppingDict['productlist'][i][inputlist[index][1]]}
            showproductsonfiguration+= inputlist[index][1] + " : " + linevalue + "<br />";
            }
        else if(inputlist[index][2]=='font-size'){
            if(ShoppingDict['productlist'][i][inputlist[index][1]]==''){linevalue='<font>standartinis teksto dydis</font>'}
            else{linevalue=ShoppingDict['productlist'][i][inputlist[index][1]]}
            showproductsonfiguration+= inputlist[index][1] + " : " + linevalue + "<br />";
            }
        else if(inputlist[index][2]=='img'){
            if(ShoppingDict['productlist'][i][inputlist[index][1]]==''){linevalue='<font color="red">neįkeltas paveikslėlis!</font>'}
            else{linevalue='<img src="'+ShoppingDict['imglist'][ShoppingDict['productlist'][i][inputlist[index][1]]]+'" style="max-width:100px;  max-height:100px;"'+'>'}
            showproductsonfiguration+= inputlist[index][1] + " : " + linevalue + "<br />";
        }

    showproductsonfiguration+='<br>'
    };
    showproductsonfiguration+='<br><p>-------<p><br>'
    document.getElementById('productlistmodalcontent').innerHTML=showproductsonfiguration;
    };
    };




function selectProductNum(){
    var selectedproduct=document.getElementById('selectproduct').value
    document.getElementById('numofproduct').innerHTML = selectedproduct;
    for (i = 0; i < featurenumber; i++) {
        console.log(i)
        if (inputlist[i][2]=="text"){
           var idname='textfor'+inputlist[i][4];
           newfieldvalue=ShoppingDict['productlist'][selectedproduct-1][inputlist[i][1]];
           document.getElementById(idname).value = newfieldvalue;

            document.getElementById(inputlist[i][4]).innerHTML = newfieldvalue;
            var stringData = document.getElementById('svg2').outerHTML;
            document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;

        }

        else if (inputlist[i][2]=="font-size"){
           var idname='fontsizefor'+inputlist[i][4];
           newfieldvalue=ShoppingDict['productlist'][selectedproduct-1][inputlist[i][1]];
           document.getElementById(idname).value = newfieldvalue;
            document.getElementById(inputlist[i][4]).style.fontSize = newfieldvalue;
            var stringData = document.getElementById('svg2').outerHTML;
            document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;

        }

        else if(inputlist[i][2]=="img"){
            var idname='imgfor'+inputlist[i][4]
            console.log(idname);
                inputpath=ShoppingDict['productlist'][selectedproduct-1][inputlist[(i)][1]]
                if(inputpath in ShoppingDict['imglist']==true){
                    baseimage=ShoppingDict['imglist'][inputpath]
                }
                else{baseimage='';}
                    var im = document.getElementById(inputlist[(i)][4]);
                    im.setAttribute('xlink:href',baseimage);
                    var stringData = document.getElementById('svg2').outerHTML;
                    document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;

                    document.getElementById('imgtoshow'+inputlist[(i)][4]).src=baseimage;
                    document.getElementById(idname).value = ''



        }
}
    document.getElementById("changetextureURLfrominputvalue").click();
    document.getElementById("currentproductselected").innerHTML=selectedproduct;

};





function emptyproductdict(){
    selectproductmenuShowHide()
    var returndict={}
    for(i=0; i<featurenumber; i++){
            if(inputlist[i][2]=='font-size'){
                returndict[inputlist[i][1]]=inputlist[i][5]
            }
            else{
                returndict[inputlist[i][1]]=''
            };
        };
        return returndict;///////////grazina pvz.:{Gaminio antraštė: "", Gaminio paveikslelis: ""}
};

/////////////jei q=1 funkcija veikia lyg uzkrautu produkta pirma karta ir uzkrautu vienos prekes pasirinkima
function refreshProductNumber(q){
    var oldnumber=ShoppingDict['productlist'].length;
    var newnumber=document.getElementById('productsNumber').value
    if (q==1){newnumber=1};

    if (checkInp(newnumber)==false||newnumber==0||newnumber>200){
        if(newnumber>200){
            alert('Maksimalus vieno pirkimo pirkinių skaičius=200, norėdami pirkti daugiau įkelkite šias 200 prekių į krepšelį, ir pakartotinai įkelkite į krepšelį trūkstamą kiekį prekių.')
            newnumber=200
        }
        else{
        newnumber=oldnumber
        console.log(newnumber)};
    };
    document.getElementById('productsNumber').value=newnumber;
    if(newnumber>oldnumber){
        var diffrence=newnumber-oldnumber
        ///////////////Idedam tiek tusciu produktu kiek reikia
        for(a = 0; a < diffrence; a++){
            ShoppingDict['productlist'].push(emptyproductdict())
        }}

    else if(newnumber<oldnumber){
        ShoppingDict['productlist'].splice(newnumber, oldnumber-1);
    };

    selectproductmenuShowHide(newnumber)
    document.getElementById('howmuchproducts').innerHTML=newnumber
    document.getElementById('numselectorlabel').innerHTML='Konfigūruojamas produktas('+newnumber+'):';
    console.log(ShoppingDict['productlist'])

};

refreshProductNumber(1);





function addProductSelector(){
    var newButton = document.createElement("BUTTON");
    var text = document.createTextNode("This is a button");
    newButton.setAttribute("class", "page-item");
    newButton.appendChild(text);
    var placetoinsert = document.getElementById('choseproducttoconfigure');
    placetoinsert.insertBefore(newButton, placetoinsert.childNodes[0]);
};

//////////Funkcija pakeicianti verte prekes dictionary
function setvalueindict(type, inputname, value, base64image){//////////////featuretochange yra pvz dicte Antraste:Namas tai featuretochange=antraste, value namas
    if(type=='text'){
    productnumber=document.getElementById('numofproduct').innerHTML;
    ShoppingDict['productlist'][productnumber-1][inputname]=value
    console.log(ShoppingDict['productlist'][productnumber-1][inputname]);
    }
    else if(type=='img'){
    productnumber=document.getElementById('numofproduct').innerHTML;
    productpath=document.getElementById(value).value;
    ShoppingDict['productlist'][productnumber-1][inputname]=productpath;
    ShoppingDict['imglist'][productpath]=base64image;
    console.log(ShoppingDict['imglist'])
    }
    else if(type=='font-size'){
    productnumber=document.getElementById('numofproduct').innerHTML;
    ShoppingDict['productlist'][productnumber-1][inputname]=value
    }

};






function validateImage(inputid) {
    var formData = new FormData();

    var file = document.getElementById(inputid).files[0];

    formData.append("Filedata", file);
    var t = file.type.split('/').pop().toLowerCase();
    if (t != "jpeg" && t != "jpg" && t != "png" && t != "bmp" && t != "gif" && t != "svg") {
        alert('Prašome pasirinkti vieną iš šių failo formatų: jpeg/jpg/png/bmp/svg');
        document.getElementById(inputid).value='';
        return false;
    }
    if (file.size > 1024000*10) {
        alert('Maksimalus įkeliamo failo dydis: 10 MB');
        document.getElementById(inputid).value='';
        return false;
    }
    return true;
};









/////////////////////////////////////////////////////////////////////////////////////
function setImage(inputid, outputid, inputname, imgtoshow)
{

    if(validateImage(inputid)==true){

    var dataurl = null;
    var filesToUpload = document.getElementById(inputid).files;
    var file = filesToUpload[0];

    // Create an image
    var img = document.createElement("img");
    // Create a file reader
    var reader = new FileReader();
    // Set the image once loaded into file reader



    if(document.getElementById(inputid).value in ShoppingDict['imglist'] == false){
    reader.onload = function(e)
    {
        img.src = e.target.result;

        img.onload = function () {
            var canvas = document.createElement("canvas");
            var ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);

            var MAX_WIDTH = 800;
            var MAX_HEIGHT = 800;
            var width = img.width;
            var height = img.height;

            if (width > height) {
              if (width > MAX_WIDTH) {
                height *= MAX_WIDTH / width;
                width = MAX_WIDTH;
              }
            } else {
              if (height > MAX_HEIGHT) {
                width *= MAX_HEIGHT / height;
                height = MAX_HEIGHT;
              }
            }
            canvas.width = width;
            canvas.height = height;
            var ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, width, height);

            baseimage = canvas.toDataURL("image/jpeg");
            var im = document.getElementById(outputid);
            im.setAttribute('xlink:href',baseimage);
            var stringData = document.getElementById('svg2').outerHTML
            document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
            document.getElementById("changetextureURLfrominputvalue").click();
            setvalueindict('img', inputname, inputid, baseimage);
            document.getElementById(imgtoshow).src=baseimage;
        } // img.onload
    }
    reader.readAsDataURL(file);}
    };////baigeiasi if validate image



    if(document.getElementById(inputid).value in ShoppingDict['imglist']==true){////////////////JEI IMG JAU IDETAS I DICT DARYTI TAPATI TIK PAIMANT IMG IS DICTO
    var im = document.getElementById(outputid);
    baseimage=ShoppingDict['imglist'][document.getElementById(inputid).value]
    im.setAttribute('xlink:href',baseimage);
    var stringData = document.getElementById('svg2').outerHTML
    document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
    document.getElementById("changetextureURLfrominputvalue").click();
    document.getElementById(imgtoshow).src=baseimage;
    productnumber=document.getElementById('numofproduct').innerHTML;
    productpath=document.getElementById(inputid).value;
    ShoppingDict['productlist'][productnumber-1][inputname]=productpath;
    };



};
















function setImage1(inputid, outputid, inputname, imgtoshow) {
    if(validateImage(inputid)==true){

  var file    = document.querySelector('#'+inputid).files[0];
  var reader  = new FileReader();
console.log(document.getElementById(inputid).value)

if(document.getElementById(inputid).value in ShoppingDict['imglist'] == false){///JEI IMG DAR NEIKELTAS I DICT TAI IKELT I DICT>>ikelt ant 3d
  reader.addEventListener("load", function () {
  var im = document.getElementById(outputid);
  baseimage=reader.result;

im.setAttribute('xlink:href',baseimage);
  var stringData = document.getElementById('svg2').outerHTML
document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
document.getElementById("changetextureURLfrominputvalue").click();
setvalueindict('img', inputname, inputid, baseimage);


  }, false);


  if (file) {
    reader.readAsDataURL(file);
  }}}
if(document.getElementById(inputid).value in ShoppingDict['imglist']==true){////////////////JEI IMG JAU IDETAS I DICT DARYTI TAPATI TIK PAIMANT IMG IS DICTO
    var im = document.getElementById(outputid);
    baseimage=ShoppingDict['imglist'][document.getElementById(inputid).value]
    im.setAttribute('xlink:href',baseimage);
    var stringData = document.getElementById('svg2').outerHTML
    document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
    document.getElementById("changetextureURLfrominputvalue").click();


    productnumber=document.getElementById('numofproduct').innerHTML;
    productpath=document.getElementById(inputid).value;
    ShoppingDict['productlist'][productnumber-1][inputname]=productpath;

};

};




function refreshFunction(inputid, targetid, inputname) {
    inputtext=document.getElementById(inputid).value;
    setvalueindict('text', inputname, inputtext);/////////////<<siunciam kad atnaujintu reiksme dicte

    document.getElementById(targetid).innerHTML = inputtext;
    var stringData = document.getElementById('svg2').outerHTML

    document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
    document.getElementById("changetextureURLfrominputvalue").click();

};


function setFontSize(inputid, targetid, inputname) {
    inputtext=document.getElementById(inputid).value;

    document.getElementById(targetid).style.fontSize = inputtext;
    var stringData = document.getElementById('svg2').outerHTML;
    setvalueindict('font-size', inputname, inputtext);/////////////<<siunciam kad atnaujintu reiksme dicte

    document.getElementById("input").value = 'data:image/svg+xml;utf8,'+stringData;
    document.getElementById("changetextureURLfrominputvalue").click();

};







///////////////////////////////////////////////Funkcija postinanti iskvieciama taip: post('/contact/', {name: 'Johnny Bravo'});
function post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}
refreshProductNumber(10);



function displaycartnumberinnav(){
    cartcontent=JSON.parse(localStorage.getItem("cart"))
    num=cartcontent.length;
    document.getElementById('productsNumber').innerHTML=num;
};
displaycartnumberinnav()









</script>