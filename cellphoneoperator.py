import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

def setpayment(name, amount, fullmessage):
    orderlist_file='fileID'

    scope=['https://www.googleapis.com/auth/drive']
    credentials= ServiceAccountCredentials.from_json_keyfile_name('shop/creds.json', scope)
    client=gspread.authorize(credentials)
    date=datetime.datetime.now()
    sheet=client.open_by_key(orderlist_file)
    sheet=sheet.worksheet('devyniolikti')
    paymentslist=sheet.col_values(1)

    row=[len(paymentslist), str(date), name, amount, fullmessage, 'NoneYet']
    sheet.append_row(row)
    return row