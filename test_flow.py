#!/usr/bin/env python3
"""Full flow integration test for dashboard generator."""

import requests
import sys
import json

BASE = 'http://localhost:5000'

def check(label, ok):
    print(f'  {label}: {"✅" if ok else "❌"}')
    return ok

# 1. Upload
print('1️⃣  Upload')
r = requests.post(f'{BASE}/api/upload', files=[
    ('files', ('test_業績.xlsx', open('/home/cryptochyi629/Dashboard_Gen/excel-dashboard/test_業績.xlsx', 'rb')))
])
assert r.status_code == 200
data = r.json()
session_id = data['session_id']
print(f'  Session: {session_id}')
check('file parsed', len(data['files']) == 1)
check('sheet detected', len(data['files'][0]['sheets']) == 1)

# 2. Analyze
print('2️⃣  Analyze')
r = requests.post(f'{BASE}/api/analyze', json={
    'session_id': session_id,
    'selections': [{'filename': 'test_業績.xlsx', 'sheetName': '各部門業績'}]
})
assert r.status_code == 200
data = r.json()
suggestions = data.get('suggestions', [])
check('suggestions returned', len(suggestions) > 0)
print(f'  {len(suggestions)} charts: {[s["type"] for s in suggestions]}')

# 3. Generate
print('3️⃣  Generate')
r = requests.post(f'{BASE}/api/generate', json={
    'session_id': session_id,
    'selections': [{'filename': 'test_業績.xlsx', 'sheetName': '各部門業績'}],
    'refinements': '深色主題戰情表'
})
assert r.status_code == 200
data = r.json()
version = data['version']
check('version returned', version > 0)
print(f'  Version: {version}')

# 4. Dashboard page
print('4️⃣  Dashboard HTML')
r = requests.get(f'{BASE}/dashboard/{session_id}/{version}')
assert r.status_code == 200
html = r.text
checks = {
    'doctype': '<!DOCTYPE html>' in html,
    'echarts': 'echarts' in html.lower(),
    'charts': 'echarts' in html.lower() or 'chart' in html.lower(),
    'vue': 'vue' in html.lower(),
    'kpi_cards': 'kpi' in html.lower() or 'card' in html.lower(),
}
all_ok = True
for k, v in checks.items():
    all_ok = check(k, v) and all_ok
print(f'  size: {len(html)} bytes')

# 5. Versions API
print('5️⃣  Versions API')
r = requests.get(f'{BASE}/api/versions/{session_id}')
assert r.status_code == 200
vers = r.json().get('versions', [])
check('version persisted', len(vers) >= 1)

print()
if all_ok:
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(' ✅  ALL TESTS PASSED')
    print(' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    sys.exit(0)
else:
    print(' ❌  SOME TESTS FAILED')
    sys.exit(1)
