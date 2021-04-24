# flask-shop<br>
Been making this eshop for my needs, but it expanded a lot more than I expected at first<br>
# Currently this e shop has stable functions:<br>
-----USER SIDE-----<br>
*Product suggestions on main page shown by selected product features and categories<br>
*Product search<br>
*3D product customizator<br>
*2D product customizator<br>
*Product cart showing customized product data<br>
*Invoice pdf generator<br>
*automatic email of order status and invoices<br>
------ADMIN SIDE-----<br>
*Data that needs to be loaded quickly is stored in server, but order data and many settings are set in google spreadsheet and disc<br>
*Most of dynamic content is edited in google spreadsheet<br>
*Customized products SVG files(ready for manufacture) are auto-generated and stored to selected Google Drive folder<br>
*Orders data are auto-stored and updated in google spreadsheet and can be easily edited<br>
*Dynamic shop content is edited in google spreadsheet file<br>
*Shop admin page with functions: update order status/send, edit invoices/preview order content<br>
*If shop crashes all orders data are accesible and editable in google cloud<br>
<br>
#Shop requires:<br>
Frontend: Bootstrap, Verge3d(for 3d scenes), Fontawesome, LightBox<br>
Backend python libraries: gspread, json, oauth2client, pydrive.drive, pydrive.auth, BeautifulSoup, cssutils, csv, flask, flask_weasyprint, werkzeug.utils, flask_basicauth<br>
<br>

# Methods of uploading products to store(LTU lang):
```
----------------------1. SVG Pritaikymas e shopui (Inkscape)-------------------------<br>
main.svg<br>
1. uzdedu teksta gaminio isoreje su tekstu "orderid"<br>
2. Uzdedu kvadrata par visa gaminio plota. sita kvadrata idedu i apatini layer kad butu fone. Nustatau spalva-balta.<br>
3. Lenkta teksta daryti pagal tokia seka:<br>
	1)sukuriu teksta, bet ne textboxa, parasau teksta, nustatau centruoti(arba nuo krasto pozicija)<br>
	2)nustacius pozicija, pasirinkti patha+teksta ir tada text>put on path<br>
	3)issaugoti kaip test.svg ir paziureti ar tekstas browseryje atrodo taip pat kaip inkscape<br>
4. issaugau kaip main.svg<br>
<br>
contours.svg<br>
1. palieku tik konturus. uzdedu spalva ant pavirsiu. jei atskiri konturai reikia padaryti path>combine<br>
2. istrinu fonini kvadrata, visus rasterius palieku tik pjuvio kontura.<br>
3. issaugau plain svg formatu faila contours.svg<br>
	jei blenderis kazkaip atidaro negerai galima pabandyt padaryti path>union<br>
<br>
svg for production.svg<br>
1. atidarau main.svg<br>
2. nuimu balto fono kvadrata<br>
3. pathai skirti teksto islenkimui turi buti nematomi<br>
4. issaugau plain svg kaip "svg for production.svg"<br>
5. atsidarau su notepadu. Randu tspana su tekstu "orderid". Pakeiciu sito tspano id i "orderid"<br>
<br>
svg for customizator.svg<br>
1. atidarau main.svg<br>
2. deletinu pjuvio linijas<br>
3. pathai skirti teksto islenkimui turi buti nematomi<br>
4. teksto laukeliuose istrinti teksta<br>
5. issaugau kaip plain svg pavadinimu svg for customizator.svg<br>
6. atsidarau su notepadu. Pakeiciu faile simboli "#" i "%23"<br>
7. Svg faile pradzioje uz <svg> ikeliu toki turini su FONTO PAVADINIMU, fonto failo tipu ir fontu paverstu i base64:<br>
<defs><br>
  <style type="text/css"><br>
    @font-face {<br>
      font-family: "fonto pavadinimas be kabuciu";<br>
      src: url(data:font/"FAILO TIPAS BE KABUCIU PVZ: ttf";charset=utf-8;base64,"CIA IKELTI BASE64 TEKSTA NENAUDOJANT KABUCIU. NEPADARYTI TARPO TARP KABLELIO IR BASE64!"<br>
);<br>
    }<br>
  </style><br>
</defs>"<br>
8. istrinti virsuje nereikalinga eilute:<br>
<?xml version="1.0" encoding="UTF-8" standalone="no"?><br>
9. <svg> tage idedu id='svg2'<br>
<br>
<br>
----------------------2. Setting up 3D scene in Blender3D:<br>-------------------------<br>
1. import svg<br>
2. pazymeti svg>   object>convert to>mesh from curve<br>
3. Pazymeti visus face>extrude pagal medziagos stori<br>
4. padidint kad butu patogu dirbti<br>
5. eiti i uv aplinka. pazymeti modelio front face>desinys click>UV...>project from view(bonus). Nugarinis face be engravingo uv mapa nunest uz image ribu, kad ant jo neuzsikeltu engraved tekstura(kuri nera repeatable)<br>
6. Sudeti pjuvius(seam) ant sieneliu. Padaryti paprasta unwrap sienoms.<br>
7. pasirinkti objekta. Sone prie materials turi buti 2 materials: Front, Side<br>
8. Priskirti kiekvienam is materials pavirsius, spaudziant 'Assign'. <br>
9. issaugau blend faila verge produkto appse<br>
10. exportinu gltf i verge produkto appsa<br>
```
