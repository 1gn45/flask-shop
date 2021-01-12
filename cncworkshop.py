import gspread
import json
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import csv
from flask import flash, request
import uuid

credentialsfile= 'shop/creds.json'
serverfolder= 'shop'
currentToollistfileid='fileID'
wornouttoolsfileid='fileID'
f360toollibrries={'Datron':'DATRON-DATRON Cutting Tools.json'}
toolinputdata={'type':['flat end mill', "ball end mill", "bull nose end mill", "radius mill", "spot drill", "drill"], 'vendor':'who manufacture this', 'D1':'tool diameter', 'D2':'tool holder diameter', 'flutes':'number of flutes', 'L2':'tool flute length', 'L3':'tool max working depth', 'L1':'tool length', 'R':'tool radius', 'angle':'drill angle', 'description':'about tool'}


def addtool(tool):

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name(credentialsfile, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    currenttools=getdrivefile(currentToollistfileid)
    currenttools['data'].append(tool)

    currenttools['modified']=str(datetime.datetime.now())
    currenttools['version']=1

    newtoolslist=json.dumps(currenttools, indent=4)
    file1 = drive.CreateFile({'id': currentToollistfileid})
    file1.SetContentString(newtoolslist)
    file1.Upload()
    return currenttools






def toolcutingfeedsspeeds(d, type):
    if type=='drill':
        if d<5:
            rpm=15000
            fpf=500
            plungespeed=500
        elif 5<=d<7:
            rpm=13000
            fpf=500
            plungespeed=500
        elif 7<=d:
            rpm=6000
            fpf=300
            plungespeed=300



    else:
        if d<1:
            fpf=0.005
            rpm=40000
        elif 1<=d<1.5:
            fpf=0.014
            rpm=40000
        elif 1.5<=d<2:
            fpf=0.037
            rpm=40000
        elif 2<=d<3:
            fpf=0.52
            rpm=38000
        elif 3<=d<6:
            fpf=0.088
            rpm=38000
        elif 6<=d<8:
            fpf=0.111
            rpm=36000
        elif 8<=d<10:
            fpf=124
            rpm=34000
        elif 10<=d<12:
            fpf=0.141
            rpm=32000
        elif 12<=d<16:
            fpf=0.075
            rpm=32000
        elif 16<=d<20:
            fpf=0.063
            rpm=32000
        elif 20<=d:
            fpf=0.063
            rpm=36000

        if d<12:
            feed=fpf*rpm
        elif d>=12:
            feed=fpf*rpm*2
        plungespeed=feed/4

    return {'feed':feed, 'rpm':rpm, 'fpf':fpf, 'plungespeed':plungespeed}


def toolholdernumber(d, type):
    if type=='flat end mill':
        if d==6:
            return 5
        elif d==8:
            return 4
        elif d==10:
            return 3
        elif d==5:
            return 6
        elif d<5:
            return 7

    elif type=='ball end mill':
        return 8
    elif type=='bull nose end mill':
        return 8
    elif type=='radius mill':
        return 6
    elif type=='spot drill':
        return 9
    elif type=='drill':
        return 1
    elif type=='form mill':
        return 2
    elif type=='face mill':
        return 10

    else:
        return 3





def addtoolfromlibrary():
    selecttoollibrary=request.form.getlist('selecttoollibrary')
    pridnum=request.form.get('pridnum')
    pridnum=pridnum.lower()
    toolcondition=request.form.get("toolcondition")
    with open(serverfolder+'/toollibraries/'+f360toollibrries[selecttoollibrary[0]], 'r') as u:
        lib=json.loads(u.read())
    counter=0
    for a in lib['data']:
        toolfromlib=a['product-id'].lower()
        if pridnum in toolfromlib:
            if toolfromlib.endswith(pridnum):
                counter+=1
                selectedtool=a

    if counter>1:
        flash('pagal nurodyta id yra daugiau nei 1 variantas')
        return None
    elif counter==0:
        return None
    elif counter==1:
        ss=selectedtool
        selectedtool["post-process"]['number']=toolholdernumber(selectedtool['geometry']['DC'], selectedtool['type'])
        feeds=toolcutingfeedsspeeds(selectedtool['geometry']['DC'], selectedtool['type'])
        selectedtool["start-values"]["*"]['n']=feeds['rpm']
        selectedtool["start-values"]["*"]['n_ramp']=feeds['rpm']
        selectedtool['start-values']["*"]["v_f"]=feeds['feed']
        selectedtool['start-values']["*"]["v_f_leadIn"]=feeds['feed']
        selectedtool['start-values']["*"]["v_f_leadOut"]=feeds['feed']
        selectedtool['start-values']["*"]["v_f_plunge"]=feeds['plungespeed']
        selectedtool['start-values']["*"]["v_f_retract"]=feeds['feed']
        selectedtool['start-values']["*"]["f_n"]=feeds['feed']/feeds['rpm']
        selectedtool['description']=selectedtool['description']+' '+ toolcondition
        selectedtool["guid"]=str(uuid.uuid1())
        selectedtool['tool added date']=str(datetime.datetime.now())
        addtool(selectedtool)


        return selectedtool



    return 'a'


def getdrivefile(fileid):
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name(credentialsfile, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    currentToollist = drive.CreateFile({'id': fileid})
    currentToollist.GetContentFile('shop/tmp/orderdict.json')
    with open(serverfolder+'/tmp/orderdict.json', 'r') as u:
        file1=json.loads(u.read())
        return file1

def removetools(tools, currenttools):
    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name(credentialsfile, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    currenttools=currenttools

    removabletools=[]
    index=0
    flash(str(tools))

    for e in tools:
        if str(e) in str(currenttools):
            index=currenttools['data'].index(e)
            removabletools.append({str(datetime.datetime.now()):e})
            del currenttools['data'][index]
    if len(removabletools)!=0:
        currenttools['modified']=str(datetime.datetime.now())
        currenttools['version']=1



    wornouttools = drive.CreateFile({'id': wornouttoolsfileid})
    wornouttools.GetContentFile('shop/tmp/orderdict.json')
    with open(serverfolder+'/tmp/orderdict.json', 'r') as u:
        wwornouttools=json.loads(u.read())
    wwornouttools+=removabletools
    newwornouttoolslist=json.dumps(wwornouttools, indent=4)
    wornouttools.SetContentString(newwornouttoolslist)
    wornouttools.Upload()

    newtoolslist=json.dumps(currenttools, indent=4)
    file1 = drive.CreateFile({'id': currentToollistfileid})
    file1.SetContentString(newtoolslist)
    file1.Upload()


    return currenttools