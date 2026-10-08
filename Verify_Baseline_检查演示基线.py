"""Read-only competition preflight; run after resetting the fictional local demo."""
import json
import urllib.request
from backend.fixtures_演示案例 import PROFILES, EXPECTED_RESULTS

def get(path, account='A'):
    request = urllib.request.Request('http://127.0.0.1:8000/api'+path,
        headers={'X-Demo-Account':account})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)

def main():
    health = get('/health')
    assert health['demo_time'] == '2026-10-07T10:00:00+09:00'
    assert health['timezone'] == 'Asia/Seoul' and health['fictional_data']
    assert health['mode'] == 'fixed_demo', 'Preflight expects the fixed-demo competition mode.'
    expected = EXPECTED_RESULTS
    profiles = PROFILES
    actual = {}
    for account in ['A','B','C']:
        assert get('/profile',account) == profiles[account], account+' profile was changed; reset first.'
        notices = sorted(get('/notices',account), key=lambda item:item['id'])
        assert [item['id'] for item in notices] == ['N1','N2','N3','N4','N5']
        assert all(item['version'] == 1 and item['publication_status'] == 'approved' for item in notices)
        actual[account] = [item['match']['status'] for item in notices]
        assert actual[account] == expected[account], account+' does not match the expected matrix.'
        assert get('/cases',account) == []
        for notice in notices:
            detail = get('/notices/'+notice['id'],account)
            assert detail['tasks'] == []
            assert detail['sharing_scope'] == 'none'
            assert detail['submission_status'] == {'status':'not_reported', 'school_received':False, 'school_approved':False}
    assert get('/cases','staff') == []
    assert len(get('/notices','staff')) == 5
    print('PASS: fixed clock, 15 matching results, original profiles, v1 notices, no tasks/cases/sharing/submission.')

if __name__ == '__main__':
    main()
