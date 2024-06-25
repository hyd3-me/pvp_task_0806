import requests, random, json, csv
from urllib.parse import urlparse
from urllib.parse import parse_qs
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import argparse
import time


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
    print(f'{_fname} has been writed')
    return 0

def update_data_from_hot(_data_storage, _data_list):
    for tweet_info in _data_list:
        # собираем данные из твитов в один список
        _data_storage.append([tweet_info['created_at'], tweet_info['id'], tweet_info['user']['id'], tweet_info['user']['screen_name'], tweet_info['text_raw'], tweet_info['reposts_count'], tweet_info['comments_count'], tweet_info['attitudes_count']])
    return 0, _data_storage

def get_json_data_from_hotline(_sess_object, _url):
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
    _file_name = 'weibo_tweet_info.csv'
    err = write_csv(_file_name, _final_data_storage)
    return 0, _final_data_storage

def check_allow_coms(_sess_object, _post_id):
    # is allow coms?
    check_comm_url = f'https://weibo.com/ajax/statuses/checkAllowCommentWithPic?id={_post_id}'
    resp_allow_comm = _sess_object.get(check_comm_url)
    status = resp_allow_comm.json().get('ok', '')
    if not status:
        return 1, f'comments not allowed'
    return 0, resp_allow_comm.json().get('result', '')

def get_json_data_from_coms(resp_obj):
    comm_text = resp_obj.text
    comm_json_data = json.loads(comm_text)
    return 0, comm_json_data

def get_head_comms(_sess_object, _post_id, _user_id):
    first_comm_url = f'https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&count=20&type=feed&uid={_user_id}&fetch_level=0&locale=en-US'
    head_comm_resp = _sess_object.get(first_comm_url)
    if head_comm_resp.status_code != 200:
        msg = 'head_comm status code != 200'
        return 1, msg
    err, json_data_from_coms = get_json_data_from_coms(head_comm_resp)
    if err:
        return 1, f'error in extract data from resp'
    return 0, json_data_from_coms

def update_list_coms(_storage, _data_list, _post_id):
    for comm in _data_list:
        _storage.append([comm['created_at'], _post_id, comm['id'], comm['user']['id'], comm['user']['screen_name'], comm['text_raw'], comm['like_counts'], comm['rootid']])
        _nested_coms = comm.get('comments')
        if _nested_coms:
            err, _storage = update_list_coms(_storage, _nested_coms, _post_id)
    return 0, _storage

def get_f1_comm(_sess_object, _post_id, _user_id):
    next_url = f'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&count=10&uid={_user_id}&fetch_level=0&locale=en-US'
    resp = _sess_object.get(next_url)
    if resp.status_code != 200:
        msg = 'next_comm status code != 200'
        return 1, msg
    err, json_data_from_coms = get_json_data_from_coms(resp)
    if err:
        return 1, f'error in extract data from resp'
    return 0, json_data_from_coms

def get_next_com(_sess_object, _post_id, _user_id, _max_id):
    next_com_url = f'https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={_post_id}&is_show_bulletin=2&is_mix=0&max_id={_max_id}&count=20&uid={_user_id}&fetch_level=0&locale=en-US'
    resp = _sess_object.get(next_com_url)
    if resp.status_code != 200:
        msg = 'next_comm status code != 200'
        return 1, msg
    err, json_data_from_coms = get_json_data_from_coms(resp)
    if err:
        return 1, f'error in extract data from resp'
    return 0, json_data_from_coms

def get_comms_list_from_tweet(_sess_object, _post_id, _user_id):
    _pre_data = []
    err, _resp = check_allow_coms(_sess_object, _post_id)
    if err:
        return 1, _resp
    err, _json_data = get_head_comms(_sess_object, _post_id, _user_id)
    if err:
        return 1, _json_data
    err, _pre_data = update_list_coms(_pre_data, _json_data.get('data'), _post_id)
    err, _json_data = get_f1_comm(_sess_object, _post_id, _user_id)
    if err:
        return 1, _json_data
    err, _pre_data = update_list_coms(_pre_data, _json_data.get('data'), _post_id)
    _max_id = _json_data.get('max_id')
    # get next1
    err, _json_data = get_next_com(_sess_object, _post_id, _user_id, _max_id)
    if err:
        return 1, _json_data
    err, _pre_data = update_list_coms(_pre_data, _json_data.get('data'), _post_id)
    _max_id = _json_data.get('max_id')
    # get next2
    err, _json_data = get_next_com(_sess_object, _post_id, _user_id, _max_id)
    if err:
        return 1, _json_data
    err, _pre_data = update_list_coms(_pre_data, _json_data.get('data'), _post_id)
    _max_id = _json_data.get('max_id')
    #while max_id comments is allow
    return 0, _pre_data

def parse_coms(_sess_object, _posts_list):
    _head = ['created_at', 'id', 'userid', 'username', 'text_raw', 'like_counts', 'rootid']
    _comms_list = []
    _comms_list.append(_head)
    for post in _posts_list[1:]:
        err, _new_comms_list = get_comms_list_from_tweet(_sess_object, post[1], post[2])
        if err:
            return 1, _new_comms_list
        for _comm in _new_comms_list:
            _comms_list.append(_comm)
    _file_name = 'weibo_comments.csv'
    err = write_csv(_file_name, _comms_list)
    if err:
        err_msg = f'{_file_name} not writed'
        return 1, err_msg
    return 0, 'ok'

async def daily_task(_args):
    print(f'{_args} started...')
    _sess_obj = get_session()
    _sess_obj = make_auth(_sess_obj)
    # num hotline updates
    _num_hl_update = 10
    err, _resp = parse_hotline(_sess_obj, _num_hl_update)
    if err:
        print(f'{_resp}')
        return err
    err, _resp = parse_coms(_sess_obj, _resp)
    if err:
        print(_resp)
        return err
    print(f'{_args} has done')
    return 0

async def main(args=[3, 30]):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_task, 'cron', hour=args[0], minute=args[1], args=['weibo daily'])
    scheduler.start()

    while True:
        await asyncio.sleep(12)

def show_help():
    print("Пример использования:\npython weibo_crawler.py -t 14 30\nАргументы:\n-t, --time: Указывает время в формате часы и минуты")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='установка таймера для скрипта')
    # Добавить флаг -t, который требует два аргумента (часы и минуты)
    parser.add_argument('-t', '--time', nargs=2, type=int, help='Флаг, требующий указание времени в формате часы и минуты', metavar=('часы', 'минуты'))
    parser.add_argument('-q', '--qqhelp', help='описание скрипта')
    args = parser.parse_args()

    if args.qqhelp:
        show_help()
    if args.time:
        # Если флаг -t указан, вызвать функцию function2 с аргументами (часы и минуты)
        asyncio.run(main(args.time))
    else:
        asyncio.run(daily_task(f'weibo once'))
