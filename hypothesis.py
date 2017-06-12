import re
import json
import config
import hashlib
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from collections import defaultdict

BASE_URL = 'https://hypothes.is/api'

def _request(endpoint, params=None):
    url = '{}{}'.format(BASE_URL, endpoint)
    params = params or {}
    headers = {
        'Authorization': 'Bearer {}'.format(config.API_TOKEN),
        'Content-Type': 'application/json;charset=utf-8'
    }
    return requests.get(url, headers=headers, params=params)


def get_urls(text):
    return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)


def screenshot(url, path):
    driver = webdriver.PhantomJS()
    driver.set_window_size(1080, 800)
    driver.set_page_load_timeout(30)
    driver.get(url)
    driver.save_screenshot(path)
    driver.quit()


if __name__ == '__main__':
    resp = _request('/profile')
    user = resp.json()
    group_id = next(g for g in user['groups'] if g['name'] == 'psyops')['id']
    resp = _request('/search', {
        'limit': 200,
        'user': user['userid'],
        'group': group_id
    })
    results = resp.json()
    total = results['total']
    data = results['rows']
    while len(data) < total:
        resp = _request('/search', {
            'limit': 200,
            'user': user['userid'],
            'group': group_id,
            'offset': len(data)
        })
        results = resp.json()
        data.extend(results['rows'])
    annos = defaultdict(lambda: dict(title='', tags=[], notes=[], annos={}))
    for d in data:
        id, uri = d['id'], d['uri']
        annos[uri]['title'] = d['document']['title'][0]
        if 'selector' in d['target'][0]:
            annos[uri]['annos'][id] = {
                'tags': d['tags'],
                'text': d['text'],
                'urls': get_urls(d['text']),
                'target': d['target'][0]
            }
        elif d['text']:
            annos[uri]['notes'].append(d['text'])
        for t in d['tags']:
            if t not in annos[uri]['tags']:
                annos[uri]['tags'].append(t)
    print('uris:', len(annos))
    print('screenshotting...')
    for uri in annos.keys():
        hash = hashlib.md5(uri.encode('utf-8')).hexdigest()
        try:
            screenshot(uri, 'shots/{}.png'.format(hash))
        except TimeoutException:
            print('failed to get screenshot for:', uri)
    json.dump(annos, open('annos.json', 'w'), sort_keys=True, indent=2)