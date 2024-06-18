import requests, random, json, csv
from urllib.parse import urlparse
from urllib.parse import parse_qs


def get_session():
    return requests.Session()

def make_auth(_sess_object):
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.5',
        'dnt': '1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
    }
    _sess_object.cookies.update(headers)

    # visit to start_page
    _home_url = 'https://weibo.com/'
    resp1 = _sess_object.get(_home_url)
    _rand_url = resp1.url
    parsed_url = urlparse(resp1.url)
    _rand = parse_qs(parsed_url.query).get('_rand')[0]

    # gather cookie, step2
    params = {
        'entry': 'miniblog',
        'a': 'enter',
        'url': _home_url,
        'domain': 'weibo.com',
        'ua': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
        '_rand': _rand,
        'sudaref': '',
    }
    url_weibo_passport_visitor = 'https://passport.weibo.com/visitor/visitor'
    resp2 = _sess_object.get(url_weibo_passport_visitor, params=params)

    # step3
    data = {
        'cb': 'visitor_gray_callback',
        'tid': '',
        'from': 'weibo',
    }
    url_gen_visitor = 'https://passport.weibo.com/visitor/genvisitor2'
    resp3 = _sess_object.post(url_gen_visitor, data=data)

    # step4
    _rand = random.random()
    s = resp3.cookies.get('SUB')
    sp = resp3.cookies.get('SUBP')
    params = {
        'a': 'crossdomain',
        's': s,
        'sp': sp,
        'from': 'weibo',
        '_rand': _rand,
        'entry': 'miniblog',
        'url': _home_url,
    }
    url_login_sina = 'https://login.sina.com.cn/visitor/visitor'
    resp4 = _sess_object.get(url_login_sina, params=params)

    # step5
    # XSRF = resp4.request._cookies.get('XSRF-TOKEN')
    # WBP = resp4.request._cookies.get('WBPSESS')
    resp5 = _sess_object.get(_home_url)
    params = {
        'url': _home_url,
    }
    url_new_login = 'https://weibo.com/newlogin'
    resp6 = _sess_object.get(url_new_login, params=params)
    return _sess_object

def read_csv(_fname):
    with open(_fname, ) as f:
        reader = csv.reader(f, delimiter = "\t")
        for row in reader:
            print(row)
    return 0

def write_csv(_fname, _data):
    with open(_fname, 'w') as _file:
        file_writer = csv.writer(_file, delimiter = "\t")
        file_writer.writerows(_data)
    return 0

def update_data_from_hot(_data_storage, _data_list):
    for tweet_info in _data_list:
        # собираем данные из твитов в один список
        _data_storage.append([tweet_info['created_at'], tweet_info['id'], tweet_info['user']['id'], tweet_info['user']['screen_name'], tweet_info['text_raw'], tweet_info['reposts_count'], tweet_info['comments_count'], tweet_info['attitudes_count']])
    return 0, _data_storage

def get_json_data_from_hotline(_sess_object, _url):
    print(_url)
    resp = _sess_object.get(_url)
    if resp.status_code != 200:
        msg = 'status code != 200'
        return 1, msg
    resp_data = resp.text
    json_data = json.loads(resp_data)
    if json_data.get('ok') != 1:
        msg = 'json data not ok'
        return 1, msg
    return 0, json_data

def parse_hotline(_sess_object, _num_hl_update):
    _max_id = 0
    _head = ['created_at', 'post_id', 'user_id', 'username', 'text_raw', 'reposts_count', 'comments_count', 'attitudes_count']
    _final_data_storage = []
    _final_data_storage.append(_head)
    for _ in range(_num_hl_update):
        update_hl_url = lambda: f'https://weibo.com/ajax/feed/hottimeline?refresh=2&group_id=102803&containerid=102803&extparam=discover|new_feed&max_id={_max_id}&count=10' if _max_id else f'https://weibo.com/ajax/feed/hottimeline?since_id=0&refresh=0&group_id=102803&containerid=102803&extparam=discover|new_feed&max_id={_max_id}&count=10'
        err, json_data = get_json_data_from_hotline(_sess_object, update_hl_url())
        if err:
            print(json_data)
            return 1, json_data
        _max_id = json_data.get('max_id')
        err, _final_data_storage = update_data_from_hot(_final_data_storage, json_data['statuses'])
        if err:
            print(_final_data_storage)
            return 1, _final_data_storage
    return 0, _final_data_storage

def get_data_from_comments(_data_list):
    # keys:
    # created_at
    # id
    # rootid
    # text
    # user
    # like_counts
    pass

def parse_comment(_sess_object, _post_id, _user_id):
    # is allow coms?
    check_url = f'https://weibo.com/ajax/statuses/checkAllowCommentWithPic?id={_post_id}'
    resp_allow_comm = _sess_object.get(check_comm)
    # resp: b'{"result":true,"ok":1}'

    _all_coms = []

    # head coms
    first_comm_url = f'https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&count=20&type=feed&uid={_user_id}&fetch_level=0&locale=en-US'
    first_comm_resp = _sess_object.get(first_comm_url)
    first_comm_text = first_comm_resp.text
    first_comm_json_data = json.loads(first_comm_text)
    # json_data keys:
    # ok # 1 is ok
    # filter_group
    # data # coms list
    # rootComment
    # total_number # coms num
    # max_id # id for fetch next coms
    # trendsText

    #get_data_from_comments(first_comm_json_data['data'])

    # more coms
    c2_url = f'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&count=10&uid={_u_id}&fetch_level=0&locale=en-US'


    # next coms with max_id
    c3_url = f'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&max_id={_max_id}&count=20&uid={_u_id}&fetch_level=0&locale=en-US'
    pass

def main():
    _sess_obj = get_session()
    _sess_obj = make_auth(_sess_obj)
    # num hotline updates
    _num_hl_update = 3
    err, _csv_data = parse_hotline(_sess_obj, _num_hl_update)
    _file_name = 'weibo_tweet_info.csv'
    err = write_csv(_file_name, _csv_data)
    if err:
        print(f'{_file_name} not writed')
        return err
    print(f'{_file_name} has been writed')


if __name__ == '__main__':
    main()