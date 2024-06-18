# pvp_task_0806 получить данные с сайта weibo.com: твиты, лайки, репосты, комментарии.
demo 

## запуск скрпита
```sh
$ python weibo_crawler.py
```
- без аргументов запустит скрипт через одну минуту
```sh
$ python weibo_crawler.py --qqhelp
```
- выведет в терминал подсказки по запуску скрипта
```sh
$ python weibo_crawler.py -t 01 12
```
- с флагом -t передаются два аргумента: первый часы и второй минуты. на это время будет установлено выполнение задачи планировщиком.

### принцип действия
- создается объект сессии
- в функции make_auth происходит сбор куков.

### главные функции:
### parse_hotline
- принимает объект сессии и количество итераций по ленте с постами в разделе /hot
- внутри собирает список постов
- вконце список записывается в файл

### parse_coms
- принимает объект сессии и список с данными о постах(_post_id, _user_id)
- сперва запрашивает доступность комментариев если, нет возврат из функции с ошибкой
- если ок, дальше происходит сбор комментариев по разным ссылкам. сперва самые верхни комментарии (5штук включая вложенные). дальше идет запрос к следующим и следом новая ссылка с параметром _max_id (что-то вроде указателя на следующий комментарий как понимаю).
- комментарии собираются в список, затем записываются все разом в файл. встречаются дубли, из-за вложенных комментариев (к ним добавляется родительский комментарий).

## полученные данные из постов записываются в weibo_tweet_info.csv файл с такими заголовками:
- created_at
- post_id
- user_id
- username
- text_raw	
- reposts_count
- comments_count
- attitudes_count

## комментарии записываются в weibo_comments.csv файл с такими заголовками:
- created_at
- id #comments_id
- userid
- username
- text_raw
- like_counts
- rootid 