import os
import json
import time
import requests
import websocket

def fetch_via_cdp(domain: str, port: str):
    pages = requests.get(f"http://127.0.0.1:{port}/json", timeout=5).json()
    wsurl = None
    for p in pages:
        if 'webSocketDebuggerUrl' in p:
            wsurl = p['webSocketDebuggerUrl']
            break
    if not wsurl:
        return None
    ws = websocket.create_connection(wsurl, timeout=5)
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Network.getCookies"}))
    res = json.loads(ws.recv())
    ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "navigator.userAgent"}}))
    ua_res = json.loads(ws.recv())
    ws.close()
    cookies = res.get('result', {}).get('cookies', [])
    pairs = [f"{c['name']}={c['value']}" for c in cookies if domain in c.get('domain','')]
    cookie_str_val = "; ".join(pairs)
    ua = ua_res.get('result', {}).get('result', {}).get('value', '')
    return cookie_str_val, ua

if __name__ == '__main__':
    port = os.environ.get('FANQIE_REMOTE_DEBUG_PORT', '9225')
    for i in range(5):
        try:
            res = fetch_via_cdp('fanqienovel.com', port)
            if res:
                cookie, ua = res
                print('cookie_len', len(cookie))
                print('ua', ua)
                print(cookie[:1000])
                break
        except Exception as e:
            print('try_err', e)
        time.sleep(1)
