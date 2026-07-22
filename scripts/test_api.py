import urllib.request, json

def get(url):
    r = urllib.request.urlopen(url)
    return json.loads(r.read())

def post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

print("Testing all endpoints through Node gateway (http://localhost:3000)...\n")

d = get('http://localhost:3000/api/hearing-problems')
print(f"[OK] hearing-problems:  {len(d)} items — first: {d[0]['title']}")

d = get('http://localhost:3000/api/adult-sections')
print(f"[OK] adult-sections:    {len(d)} items — first: {d[0]['title']}")

d = get('http://localhost:3000/api/special-tests')
print(f"[OK] special-tests:     {len(d)} items — first: {d[0]['code']}")

d = get('http://localhost:3000/api/child-categories')
print(f"[OK] child-categories:  {len(d)} items — first: {d[0]['title']}")

d = post('http://localhost:3000/api/chat', {'message': 'I hear ringing in my ears'})
print(f"[OK] /api/chat:         response length={len(d['response'])} followups={d['followups']}")

d = get('http://localhost:3000/gateway/health')
print(f"[OK] gateway/health:    status={d['status']}")

d = get('http://localhost:3000/health')
print(f"[OK] fastapi /health:   status={d['status']} uptime={d['uptime_seconds']}s")

print("\nAll endpoints OK!")
