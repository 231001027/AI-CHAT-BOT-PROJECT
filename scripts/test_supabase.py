import urllib.request, json

URL = 'https://xtzzokbmjiqmgzqsvgjg.supabase.co/rest/v1/'
KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0enpva2JtamlxbWd6cXN2Z2pnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2ODczOTMsImV4cCI6MjEwMDI2MzM5M30.ytD7C_myZnzb3j-SK052T_QRj88dZaisbThbEblkCco'
HEADERS = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}

def get(table):
    req = urllib.request.Request(URL + table + '?limit=1', headers=HEADERS)
    try:
        r = urllib.request.urlopen(req)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

for table in ['assessments', 'chat_sessions', 'chat_messages']:
    status, body = get(table)
    print(f'{table}: HTTP {status} → {body[:80]}')
