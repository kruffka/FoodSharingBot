# -*- coding: utf-8 -*-
import json
import re
import vk_api
import sqlite3
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id


# нужно в настройках api бота выставить разрешение на добавление записей стен (для wall_post_new) и входящие сообщения (messages_new)
group_id = 'Ваш id группы'
token = "Ваш токен"
access_token = "access_token (https://vk.com/dev/access_token)"


vk = vk_api.VkApi(token=token)

vk._auth_token()

api = vk.get_api()

longpoll = VkBotLongPoll(vk, group_id)
users = []

# Указываем название файла базы данных
conn = sqlite3.connect('users_database.sqlite')
cursor = conn.cursor()

# Вайтлист фудшерингов для вк бы, но там чет очень много пабликов, мб потом; пока юзеры свои любые паблики могут кидать, не больше 5
# fs_white_list = []

# Функция кнопки
def get_button(label, color, payload=''):
    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps(payload)
        },
        "color": color
    }

keyboard_city = {
    "one_time": True,
    "buttons": [
            [get_button(label="Москва", color="positive"),
             get_button(label="Санкт-Петербург", color="positive")],
            [get_button(label="Новосибирск", color="positive"),
            get_button(label="Другой", color="primary")]

        ]
}

keyboard_menu = {
    "one_time": True,
    "buttons": [
            [get_button(label="Настроить фильтр", color="positive"),
             get_button(label="Сбросить все фильтры", color="positive")],
            [get_button(label="Вкл/Выкл уведомления", color="positive"),
            get_button(label="Сменить город", color="primary")]

        ]
}

keyboard_filter = {
    "one_time": True,
    "buttons": [
            [get_button(label="Указать еду", color="positive"),
             get_button(label="Указать район/улицу", color="positive")],
            [get_button(label="Удалить из выбранного", color="positive"),
            get_button(label="Назад", color="primary")]

        ]
}

keyboard_filt_ch = {
    "one_time": True,
    "buttons": [
            [get_button(label="Показать текущий список", color="positive")],
            [get_button(label="Прекратить ввод", color="negative")]
        ]
}

# Перевести клавиатуру в строку (vk api так требует)
keyboard_city = json.dumps(keyboard_city, ensure_ascii=False).encode('utf-8')
keyboard_city = str(keyboard_city.decode('utf-8'))
keyboard_menu = json.dumps(keyboard_menu, ensure_ascii=False).encode('utf-8')
keyboard_menu = str(keyboard_menu.decode('utf-8'))
keyboard_filter = json.dumps(keyboard_filter, ensure_ascii=False).encode('utf-8')
keyboard_filter = str(keyboard_filter.decode('utf-8'))

keyboard_filt_ch = json.dumps(keyboard_filt_ch, ensure_ascii=False).encode('utf-8')
keyboard_filt_ch = str(keyboard_filt_ch.decode('utf-8'))

for event in longpoll.listen():
    # Новый пост в паблике
    # хз как с этим работать, но это наверное самый быстрый был бы способ выявляения новых постов..
    # p.s. в своем паблике все отлично работает
    if event.type == VkBotEventType.WALL_POST_NEW:
        cursor.execute('SELECT * FROM pysqlite')
        row_1 = cursor.fetchone()
        while row_1 is not None:
            if(row_1[2] == 'yes'):
                api.messages.send(peer_id=row_1[0], message="Новый пост в группе фудшеринга! https://vk.com/wall{}_{}".format(event.obj['from_id'], event.obj['id']),
                                  random_id=get_random_id())
            row_1 = cursor.fetchone()

        # r = requests.get('https://api.vk.com/method/wall.get',
        #                  params={
        #                      'access_token': access_token,
        #                      'domain': domain,
        #                      'v': '5.110',
        #                      'count': 10,
        #                      'offset': 0
        #                  })

    # Новое сообщение юзера:
    if event.type == VkBotEventType.MESSAGE_NEW:
        message = event.obj['message']

        peer_id = message['peer_id']
        text = message['text']

        # Не уверен пока насколько эта переменная может повлиять при большом кол-ве юзеров (если вообще влияет), но вроде неплохо работает
        # вроде обновляется для каждого нового сообщения и одновременно с разных акков зашло легко, буду верить в волшебство
        # идея бота странная..
        new_user = 1

        # Делаем выборку peer_id, path в таблице записей
        cursor.execute('SELECT * FROM pysqlite')
        row = cursor.fetchone()
        while row is not None:
            if(row[0] == peer_id):
                # print(row[0]) # peer_id
                # print(row[1]) # path
                # print(row[2]) # notification (y/n); 3 - fav_foov..etc; all from users_database.sqlite
                new_user = 0



                # /user - main menu
                # /user/filter - filter settings
                # /user/city - city settings
                # Идею с путями на хабре гдет подсмотрел, реализация наверное не совсем такая, мб можно все оптимизировать если было б время
                # проверки на дураков? хочу спать(
                if row[1] == '/user':

                    if text.lower() == "настроить фильтр":
                        sql_update = """UPDATE pysqlite SET path = '/user/filter' WHERE peer_id = '{}'""".format(peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filter, message="Настройки фильтра",
                                          random_id=get_random_id())

                    elif text.lower() == "вкл/выкл уведомления":
                        if row[2] == 'yes':
                            sql_update = """UPDATE pysqlite SET notification = 'no' WHERE peer_id = '{}'""".format(
                                peer_id)
                            api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Уведомления выключены",
                                              random_id=get_random_id())
                        else:
                            sql_update = """UPDATE pysqlite SET notification = 'yes' WHERE peer_id = '{}'""".format(
                                peer_id)
                            api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Уведомления включены",
                                              random_id=get_random_id())
                        cursor.execute(sql_update)
                        conn.commit()

                    elif text.lower() == "сбросить все фильтры":
                         api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Фильтры были сброшены",
                                          random_id=get_random_id())
                         sql_update = """UPDATE pysqlite SET path = '/user', links = '', fav_food = '', street = '' WHERE peer_id = '{}'""".format(peer_id)
                         cursor.execute(sql_update)
                         conn.commit()

                    elif text.lower() == "сменить город":
                        sql_update = """UPDATE pysqlite SET path = '/user/city' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_city, message="Выбор города",
                                          random_id=get_random_id())
                    else:
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Главное меню",
                                          random_id=get_random_id())

                # Выбор района/улицы в фильтре
                if row[1] == '/user/filter/dist':
                    if text.lower() == 'прекратить ввод':
                        sql_update = """UPDATE pysqlite SET path = '/user/filter' WHERE peer_id = '{}'""".format(peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filter,
                                          message="Настройки фильтра",
                                          random_id=get_random_id())
                    elif text.lower() == 'показать текущий список':
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                            message="Ваш текущий список районов/улиц для фильтра: {}".format(row[4]), random_id=get_random_id())
                    else:
                        sql_update = """UPDATE pysqlite SET street = '{}' WHERE peer_id = '{}'""".format(row[4] + " " + text.lower(), peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                          message="{} добавлен(ы) в ваш список районов/улиц для фильтра".format(
                                              re.split('[^a-zа-яё]+', text.lower(), flags=re.IGNORECASE)),
                                          random_id=get_random_id())

                # Выбор еды в фильтре
                if row[1] == '/user/filter/food':
                    if text.lower() == 'прекратить ввод':
                        sql_update = """UPDATE pysqlite SET path = '/user/filter' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filter,
                                          message="Настройки фильтра",
                                          random_id=get_random_id())
                    elif text.lower() == 'показать текущий список':
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                              message="Ваш текущий список еды для фильтра: {}".format(row[3]), random_id=get_random_id())
                    else:
                        sql_update = """UPDATE pysqlite SET fav_food = '{}' WHERE peer_id = '{}'""".format(row[3] + " " + text.lower(), peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                          message="{} добавлен(ы) в ваш список еды для фильтра".format(
                                              re.split('[^a-zа-яё]+', text.lower(), flags=re.IGNORECASE)),
                                          random_id=get_random_id())

                # удаления фильтров по отдельности
                if row[1] == '/user/filter/remove':
                    if text.lower() == 'прекратить ввод':
                        sql_update = """UPDATE pysqlite SET path = '/user/filter' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filter,
                                          message="Настройки фильтра",
                                          random_id=get_random_id())
                    elif text.lower() == 'показать текущий список':
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                            # lul
                            message="Ваш текущий список для фильтра: {}".format("Еда: " + row[3] + "; " + "Районы/улицы: " + row[4] + ";"), random_id=get_random_id())
                    else:

                        # bruh
                        # может по символам резать.. хз можно ли сломать бд если много данных туда засунуть юзером (через еду или улицы) try except v pomosh komut vidimo

                        # oof
                        if row[4].replace(text.lower(), ""):
                            sql_update = """UPDATE pysqlite SET street = '{}' WHERE peer_id = '{}'""".format(
                                row[4].replace(text.lower(), ""), peer_id)

                            cursor.execute(sql_update)
                            conn.commit()
                            # hahahah genius
                            api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                              message="{} удален из вашего списка".format(text.lower()),
                                              random_id=get_random_id())
                        else:
                            api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                              message="{} не было в списках".format(text.lower()),
                                              random_id=get_random_id())
                        # need sleep(
                        if row[3].replace(text.lower(), ""):
                            sql_update = """UPDATE pysqlite SET fav_food = '{}' WHERE peer_id = '{}'""".format(row[3].replace(text.lower(), ""), peer_id)

                            cursor.execute(sql_update)
                            conn.commit()
                # Если выбрана кнопка фильтра
                if row[1] == '/user/filter':

                    if text.lower() == "назад":
                        sql_update = """UPDATE pysqlite SET path = '/user' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Главное меню",
                                          random_id=get_random_id())

                    elif text.lower() == "указать район/улицу":
                        sql_update = """UPDATE pysqlite SET path = '/user/filter/dist' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch, message="Введите интересующие вас районы/улицы (Пример: 'Дзержинский, Кирова')",
                                          random_id=get_random_id())

                    elif text.lower() == "удалить из выбранного":
                        sql_update = """UPDATE pysqlite SET path = '/user/filter/remove' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                          message="Введите параметр, который хотели бы удалить",
                                          random_id=get_random_id())
                    elif text.lower() == "указать еду":
                        sql_update = """UPDATE pysqlite SET path = '/user/filter/food' WHERE peer_id = '{}'""".format(
                            peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filt_ch,
                                          message="Введите интересующую вас еду (Пример: 'Молоко, хлеб')",
                                          random_id=get_random_id())

                    else:
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_filter, message="Настройки фильтра",
                                          random_id=get_random_id())

                if row[1] == '/user/city':

                    if text.lower() == "москва" or text.lower() == "санкт-петербург" or text.lower() == "новосибирск":
                        sql_update = """UPDATE pysqlite SET path = '/user', city = '{}' WHERE peer_id = '{}'""".format(text.lower(), peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Вы выбрали город - {}.".format(text.lower()),
                                          random_id=get_random_id())
                    elif text.lower() == "другой":
                        sql_update = """UPDATE pysqlite SET path = '/user', city = 'another' WHERE peer_id = '{}'""".format(peer_id)
                        cursor.execute(sql_update)
                        conn.commit()
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_menu,
                                          message="Вы выбрали город - {}.".format(text.lower()),
                                          random_id=get_random_id())
                    else:
                        api.messages.send(peer_id=peer_id, keyboard=keyboard_city, message="Выбор города",
                                          random_id=get_random_id())

                break
            row = cursor.fetchone()

        # Новый юзер - спрашиваем город и добавляем в бд
        if(new_user == 1):
            if text.lower() == "москва" or text.lower() == "новосибирск" or text.lower() == "санкт-петербург" or text.lower() == "другой":
                api.messages.send(peer_id=peer_id, message="Ваш город {}!".format(text.lower()), random_id=get_random_id())
                cursor.execute(
                    "INSERT INTO pysqlite (peer_id, links, city, fav_food, street, notification, path) VALUES ({},'', '{}', '', '', 'yes', '/user')".format(
                        peer_id, text.lower()))
                conn.commit()
                api.messages.send(peer_id=peer_id, keyboard=keyboard_menu, message="Главное меню",
                                  random_id=get_random_id())
                new_user = 0
                # Вставляем в таблицу pysqlite нового пользователя

            else:

                api.messages.send(peer_id=peer_id, keyboard=keyboard_city,
                                  message="Здравствуй, я чат-бот для фудшеринга! Укажи свой город.",
                                  random_id=get_random_id())




        if text.lower() == "дай еду":
            api.messages.send(peer_id=peer_id, message="Нету еды", random_id=get_random_id())


# Закрываем соединение с базой данных
cursor.close()
conn.close()
