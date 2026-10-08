"""Reset only the fictional local demo database through its staff endpoint."""
import json
import urllib.request
import urllib.error

req = urllib.request.Request('http://127.0.0.1:8000/api/demo/reset', data=b'{}',
    headers={'Content-Type':'application/json','X-Demo-Account':'staff'}, method='POST')
try:
    with urllib.request.urlopen(req,timeout=15) as response:
        print(json.dumps(json.load(response), ensure_ascii=False))
except urllib.error.URLError:
    raise SystemExit('Start the local backend on 127.0.0.1:8000 before resetting. No real school data is touched.')
