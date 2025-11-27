import json
import browser_cookie3 as bc

domain = 'fanqienovel.com'

def get_count(func):
    try:
        jar = func(domain_name=domain)
        return len(list(jar))
    except Exception as e:
        return 'error:' + type(e).__name__

result = {
    'Chrome': get_count(bc.chrome),
    'Edge': get_count(bc.edge),
    'Firefox': get_count(bc.firefox),
}

print(json.dumps(result, ensure_ascii=False))
