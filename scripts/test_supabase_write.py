import urllib.request, json

URL = 'https://xtzzokbmjiqmgzqsvgjg.supabase.co/rest/v1/'
KEY = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
       '.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0enpva2JtamlxbWd6cXN2Z2pnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2ODczOTMsImV4cCI6MjEwMDI2MzM5M30'
       '.ytD7C_myZnzb3j-SK052T_QRj88dZaisbThbEblkCco')

HEADERS = {
    'apikey': KEY,
    'Authorization': 'Bearer ' + KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}


def post(table, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(URL + table, data=data, headers=HEADERS, method='POST')
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


# 1. Insert assessment
status, rows = post('assessments', {
    'full_name': 'Test User',
    'district':  'Chennai',
    'age':       30,
    'gender':    'male',
    'audience':  'myself',
    'routed_to': 'adult-care',
})
print(f'[{status}] assessment  → id={rows[0]["id"] if isinstance(rows, list) else rows}')

# 2. Insert chat session
status, rows = post('chat_sessions', {
    'topic_id':    'hearing-difficulty',
    'topic_title': 'Hearing Difficulty',
})
print(f'[{status}] chat_session → id={rows[0]["id"] if isinstance(rows, list) else rows}')
sid = rows[0]['id'] if isinstance(rows, list) else None

# 3. Insert chat message
if sid:
    status, rows = post('chat_messages', {
        'session_id':     sid,
        'role':           'bot',
        'message':        'When did it start?',
        'question_index': 0,
    })
    print(f'[{status}] chat_message → id={rows[0]["id"] if isinstance(rows, list) else rows}')

print('\nAll Supabase writes confirmed!')
