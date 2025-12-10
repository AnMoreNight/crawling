import requests

url = 'https://script.google.com/macros/s/AKfycbz39IOKmJgBdt4ZL2wW2eljPtdxeSrd52q0DJrXfgGnlaLQb5izqupTqSRwx1XvgqdM/exec'

print('Testing GET', url)
try:
    r = requests.get(url, timeout=15)
    print('GET status:', r.status_code)
    print('GET text (first 400 chars):')
    print(r.text[:400])
except Exception as e:
    print('GET error:', type(e).__name__, e)

print('\nTesting POST with small JSON payload (ping)')
try:
    payload = {'action': 'ping', 'data': {'test': 'ok'}}
    r = requests.post(url, json=payload, timeout=15)
    print('PING JSON POST status:', r.status_code)
    print('PING JSON POST text (first 800 chars):')
    print(r.text[:800])
except Exception as e:
    print('PING POST error:', type(e).__name__, e)

print('\nTesting POST with ingestion-style payload (one row)')
try:
    payload = {'action': 'ingest_test_rows', 'rows': [{'url':'https://example.com','companyName':'Example Inc','email':'info@example.com'}]}
    r = requests.post(url, json=payload, timeout=20)
    print('INGEST POST status:', r.status_code)
    print('INGEST POST text (first 1200 chars):')
    print(r.text[:1200])
except Exception as e:
    print('INGEST POST error:', type(e).__name__, e)

print('\nTesting POST as form-encoded (application/x-www-form-urlencoded)')
try:
    form_payload = {'action': 'ingest_test_rows', 'rows': str([{'url':'https://example.com','companyName':'Example Inc','email':'info@example.com'}])}
    r = requests.post(url, data=form_payload, timeout=15)
    print('FORM POST status:', r.status_code)
    print('FORM POST text:', r.text[:1200])
except Exception as e:
    print('FORM POST error:', type(e).__name__, e)

print('\nTesting POST with explicit JSON header')
try:
    headers = {'Content-Type':'application/json'}
    import json as _json
    r = requests.post(url, data=_json.dumps({'action':'ping'}), headers=headers, timeout=15)
    print('HEADER JSON POST status:', r.status_code)
    print('HEADER JSON POST text:', r.text[:1200])
except Exception as e:
    print('HEADER JSON POST error:', type(e).__name__, e)
