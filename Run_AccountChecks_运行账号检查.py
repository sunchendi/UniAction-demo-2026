"""Run account browser checks in a temporary database; never reset user data."""
import os
import argparse
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--demo',action='store_true',help='Run the existing 19-group competition regression in an isolated database.')
args=parser.parse_args()
browser_script='tests/browser_e2e_浏览器验证.cjs' if args.demo else 'tests/account_e2e_个人账号验证.cjs'
with socket.socket() as listener:
    listener.bind(('127.0.0.1',0))
    port=listener.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='UniActionAccountQA_') as temporary:
    env={**os.environ,'DATABASE_PATH':str(Path(temporary)/'accounts.sqlite3'),
         'DEMO_BASE_URL':f'http://127.0.0.1:{port}'}
    with (Path(temporary)/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main_主程序:app',
            '--host','127.0.0.1','--port',str(port),'--log-level','warning'],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            result=subprocess.run(['node',browser_script],cwd=ROOT,env=env)
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
    if result.returncode:
        print((Path(temporary)/'server.log').read_text(encoding='utf-8'),file=sys.stderr)
    raise SystemExit(result.returncode)
