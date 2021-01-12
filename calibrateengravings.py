import cv2
import time
import numpy as np
import time
from bs4 import BeautifulSoup
import base64



tmpfolder="shop/tmp/"


def get4edgesinimage(image):   ######funkcija paima 4 kampus is pateiktos foto
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    gray = np.float32(gray)
    corners = cv2.goodFeaturesToTrack(gray, 4, 0.01, 10)
    ##############Padarom eiliskuma nuo auksciausio tasko iki zemiausio
    listx=np.ndarray.tolist(corners)  ####paverciu tasku koordinates i pitoniska lista
    listnormal=[listx[0][0],listx[1][0],listx[2][0],listx[3][0]]
    listnormal.sort(key=lambda x: x[1])
    #################Padarom eiliskuma virsutinis kairys>vd>apatinis kairys>ad
    upperedges=listnormal[0:2]
    loweredges=listnormal[2:]
    upperedges.sort(key=lambda x: x[0])
    loweredges.sort(key=lambda x: x[0])
    li=upperedges+loweredges
    height, width, channels = image.shape
    return li, height, width





####################This function takes and evaluates its grain from dark to light(uses test file image in tmp folder)
def evaluatedigitaltestimg(): ####opens digital file of test and evaluates the brightnes range
    img1 = cv2.imread(tmpfolder+"calibrationtest.png")
    height, width, channels = img1.shape

    pts1 = np.float32([[0, 0], [1000, 0], [0, 400], [1000, 400]])
    pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    matrix = cv2.getPerspectiveTransform(pts2, pts1)
    result = cv2.warpPerspective(img1, matrix, (1000, 400))
    result=cv2.cvtColor(result,cv2.COLOR_BGR2GRAY)
    x=[0, 50]
    pixelsdarkness=[]
    while x[1]<1015:
        rangeofimage=result[100:300, x[0]:x[1]]
        a,b,c,d=cv2.mean(rangeofimage)
        pixelsdarkness.append(int(a))
        x[0]+=50
        x[1]+=50

    if pixelsdarkness[0]<pixelsdarkness[-1]:
        pixelsdarkness[0], pixelsdarkness[-1]=0, 255

        for q in range(len(pixelsdarkness)):
            if q!=0 and q!=len(pixelsdarkness)-1:
                if pixelsdarkness[q]<pixelsdarkness[q-1]:
                    pixelsdarkness[q]=pixelsdarkness[q-1]

    elif pixelsdarkness[0]>pixelsdarkness[-1]:
        pixelsdarkness[0], pixelsdarkness[-1]=255, 0

        for q in range(len(pixelsdarkness)):
            if q!=0 and q!=len(pixelsdarkness)-1:
                if pixelsdarkness[q]>pixelsdarkness[q-1]:
                    pixelsdarkness[q]=pixelsdarkness[q-1]


    return pixelsdarkness




####################This function takes a photo, finds rectangular shape in it and evaluates its grain from dark to light(uses inputed image)
def calibrateimage():
    img1 = cv2.imread(tmpfolder+"engravetest.jpg") #######Atidarau paveiksliuka is kurio noriu paimti testo kvadratuka ir ji ivertinti
    points4, height, width = get4edgesinimage(img1)#######randu kvadratuko 4 kampinius taskus

    pts1 = np.float32([[0, 0], [1015, 0], [0, 400], [1000, 400]])######nustatau i kokiu matmenu paveiksliuka ikelsiu testo kvadrata
    pts2 = np.float32([points4[0], points4[1], points4[2], points4[3]])######paruosiu 4tasku np float plota
    matrix = cv2.getPerspectiveTransform(pts2, pts1)#######################gaunu perkelimo matrica pagal kuria perktreipsiu iskreipta kvadrata i mano nustatytu matmenu kvadrata
    result = cv2.warpPerspective(img1, matrix, (1015, 400))#######Atlieku pixeliu perkelima pagal matrica
    result=cv2.cvtColor(result,cv2.COLOR_BGR2GRAY)####paverciu nespalvotai kad butu paprasciau ivertint pixeliu tamsuma
    cv2.imwrite(tmpfolder+"remappedengravetest.jpg", result)
    x=[15, 50]
    pixelsdarkness=[]
    while x[1]<1015:
        rangeofimage=result[100:300, x[0]:x[1]]
        a,b,c,d=cv2.mean(rangeofimage)
        pixelsdarkness.append(a)
        x[0]+=50
        x[1]+=50

    minvalue=min(pixelsdarkness)
    pixelsdarkness=[x-minvalue for x in pixelsdarkness]
    maxvalue=max(pixelsdarkness)#####get new maxvalue
    convertratio=255/maxvalue########get ratio to change whole list
    pixelsdarkness=[int(x*convertratio) for x in pixelsdarkness]#######convert list of pixels to values from 0 to 255
    maxvalue, minvalue=max(pixelsdarkness), min(pixelsdarkness)#######reset new max and min values needed for further operations

    if pixelsdarkness[0]<pixelsdarkness[-1]:
        pixelsdarkness[0], pixelsdarkness[-1]=0, 255

        for q in range(len(pixelsdarkness)):
            if q!=0 and q!=len(pixelsdarkness)-1:
                if pixelsdarkness[q]<pixelsdarkness[q-1]:
                    pixelsdarkness[q]=pixelsdarkness[q-1]

    elif pixelsdarkness[0]>pixelsdarkness[-1]:
        pixelsdarkness[0], pixelsdarkness[-1]=255, 0

        for q in range(len(pixelsdarkness)):
            if q!=0 and q!=len(pixelsdarkness)-1:
                if pixelsdarkness[q]>pixelsdarkness[q-1]:
                    pixelsdarkness[q]=pixelsdarkness[q-1]

    return pixelsdarkness








def handlecalibration():
    originaltestvalues=evaluatedigitaltestimg()
    uploadedtestvalues=calibrateimage()
    if originaltestvalues[0]>originaltestvalues[-1]:
        list.reverse(originaltestvalues)
    if uploadedtestvalues[0]>uploadedtestvalues[-1]:
        list.reverse(uploadedtestvalues)

    xp = uploadedtestvalues
    fp = originaltestvalues
    q=[]
    for b in range(256):
        q.append(b)
    a=np.interp(q, xp, fp)
    a=a.tolist()
    a=[int(i) for i in a]
    a[0]=0
    a[-1]=255
    doubles=set([x for x in uploadedtestvalues if uploadedtestvalues.count(x) > 1])
    if 0 in doubles:
        doubles.remove(0)
    if 255 in doubles:
        doubles.remove(255)


    doublevalues={}
    for double in doubles:
        counter=0
        sum=0
        for xpnum in range(len(xp)):
            if xp[xpnum]==double:
                counter+=1
                sum+=fp[xpnum]
        doublevalues[double]=sum/counter

######lets change values for doubles in average values
    for double in doublevalues:
        a[double]=doublevalues[double]


    makesvgssetnewproduct(a)
    return str(a)




def makesvgssetnewproduct(a):

    with open(tmpfolder+ 'workimage.svg','r') as soup:
        soup = BeautifulSoup(soup.read(), features ='xml')
        #a=soup.find('image')["xlink:href"]
        for q in soup.find_all('image'):
            data_uri=q["xlink:href"]
            img = readb64(data_uri)
            img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            counter=0
            for newpixel in a:
                img[np.where(img == [counter])] = [newpixel]
                counter+=1
            string = base64.b64encode(cv2.imencode('.jpg', img)[1]).decode()
            string='data:image/jpeg;base64,'+string
            soup.find(id= q['id'])["xlink:href"]=string
        soup.prettify()

    with open(tmpfolder+ 'workimage.svg', "w") as file:
        file.write(str(soup))

    return str(soup)

def readb64(uri):
   encoded_data = uri.split(',')[1]
   nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


   return img






