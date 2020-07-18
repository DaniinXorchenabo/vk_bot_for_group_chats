from import_libs import *
from db.controller_db import *

answers = ['Да', 'Нет', 'Не знаю', 'Сложно ответить',
           'Даже мудрецы не знают ответа на этот вопрос',
           'Не важно. Съешь яблоко!', 'А почему ты спрашиваешь?',
           'Скорее нет, чем да', 'Скорее да, чем нет',
           'Что?', 'Ты пятый раз это спрашиваешь!']

list_keys = ['user_id', "random_id", "peer_id", "domain",
             "chat_id", "user_ids", "message", "lat", "long",
             "attachment", "reply_to", "forward_messages",
             "sticker_id", "group_id", "keyboard", "payload",
             "dont_parse_links", "disable_mentions", "intent",
             "subscribe_id"]

HIGH_PRIORITY_SIGNAL = ['/stat', '/erease', "/gen", 'ask_bot']
LOW_PRIORITY_SIGNAL = ["new_words"]

COMANDS = ['/stat', '/erease', "/gen", "/kw", "/no_kw"]


class VkBot():
    vk_session = None
    run = False
    msg = dict()
    counter_msg = 0
    pool = None  # пространство с процессами
    processing_event_live = False
    sending_msg = None
    secondary_res_db = priority_rec_db = None
    obj_dict = dict()  # dict(id_chat: VkBot)

    @classmethod
    def processing_event_is_live(cls, *args, **kwargs):
        cls.processing_event_live = False

    @classmethod
    def start(cls, pool=None, lock=None, n_msg=None,
              sending_msg=None, secondary_res_db=None, priority_rec_db=None):
        cls.run = True
        cls.pool = pool
        cls.lock = lock
        cls.sending_msg = sending_msg
        cls.priority_rec_db = priority_rec_db
        cls.secondary_res_db = secondary_res_db
        cls.vk_session = VkApi(token=cfg.get("vk", "token"))
        longpoll = VkBotLongPoll(cls.vk_session, group_id=cfg.get("vk", "group"))
        print('vk bot started!')
        cls.listen_events(longpoll, n_msg=n_msg)

    @classmethod
    def listen_events(cls, longpoll, n_msg=None):
        while cls.run:
            try:
                for ev in longpoll.listen():
                    cls.processing_event(ev, n_msg=n_msg)
                cls.sending_msg_queue_processing()
            except Exception as e:
                print("произошла неизвестная ошибка в классе", cls.__name__, e)

    @classmethod
    def processing_event(cls, event, n_msg=None):
        print('something event', event)
        if event.type == VkBotEventType.MESSAGE_NEW:
            print('новое сообщение', type(event.raw), event.raw)
            if not cls.obj_dict.get(event.object.peer_id):
                cls.obj_dict[event.object.peer_id] = cls()
            print('d1')
            if WorkWithMessenges.qu_ans_test(event.object.text):
                print('d2')

                cls.sending_msg.put('func',
                                    [cls.send_msg,
                                     [WorkWithMessenges.random_answ()],
                                     cls.generate_answ_dict(event.raw)])
            else:
                print('d3')

                event_d = dict(event.raw)
                print('d3 5')
                event_d.update({'callback_func': cls.send_msg,
                                "args": [],
                                "kwargs": cls.generate_answ_dict(event_d)
                                })
                print('d3 6')
                n_msg.put(event_d)
                print('d3 7')
                if not cls.processing_event_live:  # если обработка не запущена
                    print('d4')

                    cls.processing_event_live = True
                    cls.processong_msg_class_start(n_msg)

    # ==========! work with other classes !==========
    @classmethod
    def processong_msg_class_start(cls, n_msg):
        cls.pool.apply_async(WorkWithMessenges.start,
                             args=(n_msg, cls.pool, cls.sending_msg,
                                   cls.priority_rec_db,
                                   cls.secondary_res_db),
                             callback=cls.processing_event_is_live
                             )

    # ==========! send msg !==========
    @classmethod
    def generate_answ_dict(cls, _dict: dict):
        print('d 3 5 1')
        nested_dict = []
        standart_d = {key: ((val, nested_dict.append(key))[0] if type(val) == dict else val)
                      for key, val in _dict.items() if key in list_keys}
        print('d 3 5 2')

        [standart_d.update(cls.generate_answ_dict(_dict[key])) for key in nested_dict]
        print('d 3 5 3')
        return standart_d

    @classmethod
    def sending_msg_queue_processing(cls):
        if not cls.sending_msg.empty():
            _type, material = cls.sending_msg.get()
            if _type == 'func':
                func, args, kwargs = material
                func(*args, **kwargs)

    @classmethod
    def send_msg(cls, text, *args, **kwargs):
        msg = cls.constructor_msg(text, **kwargs)

    @classmethod
    def constructor_msg(cls, text, **kwargs):
        if type(text) != str:
            if type(text) == list:
                text = ' '.join(text)
            elif type(text) == dict:
                text = ' '.join(text.keys())
            else:
                text = str(text)
            text = re_sub(r'(\s{1,})[.,!:;]', '', text)

        # характеристики сообщений чата, присущие только ему (к примеру, клавиатура)
        kwargs.update(cls.obj_dict.get(kwargs.get('peer_id', ''), dict()))
        kwargs.update({"message": text,
                       'random_id': randint(1, 2147483647),
                       })
        return kwargs

    # ==========! No classmethod !==========
    def __init__(self):
        self.unical_dict = {'keyboard': None}


class WorkWithMessenges():
    run = False
    pool = None
    sending_msg = None
    secondary_res_db = priority_rec_db = None
    qu_ans_test = lambda text: text[:4] in ['бот,', "Бот,"] and text[-1] == '?'
    random_answ = lambda: answers[randint(0, len(answers) - 1)]
    working_with_bd_pros_live = False

    @classmethod
    def working_with_bd_live(cls, *args):
        cls.working_with_bd_pros_live = False

    @classmethod
    def work_db_start(cls):
        cls.pool.apply_async(DbControl.start,
                             args=(cls.priority_rec_db,
                                   cls.secondary_res_db,
                                   cls.sending_msg),
                             callback=cls.working_with_bd_live
                             )

    @classmethod
    def start(cls, n_msg, pool, sending_msg,
              priority_rec_db, secondary_res_db):  # , n_msg=None
        try:
            print('class', cls.__name__, "started")
            cls.run = True
            cls.working_with_bd_pros_live = False
            cls.pool = pool
            cls.sending_msg = sending_msg
            cls.priority_rec_db = priority_rec_db
            cls.secondary_res_db = secondary_res_db
            cls.working_cls(n_msg=n_msg)
        except Exception as e:
            print('произошла какая-то ошибка при старте класса', cls.__name__, e)

    @classmethod
    def working_cls(cls, n_msg=None):
        while cls.run:
            try:
                cls.new_msg_queue_cheching(n_msg=n_msg)
            except Exception as e:
                print('произошла неизвестная ошибка в', cls.__name__, ":", e)
        print('class', cls.__name__, "end working")

    @classmethod
    def new_msg_queue_cheching(cls, n_msg=None):
        if not n_msg.empty():
            cls.processing_msg(n_msg.get())
        else:
            cls.run = False

    @classmethod
    def processing_msg(cls, event):
        print('пришло сообщение с текстом:', event)
        if type(event) == dict:
            text = event['object']['text']
            chat_id = event['object']['peer_id']
            callback_func = event['callback_func']
            args, kwargs = event['args'], event['kwargs']
            type_com = 'new_words' if text not in COMANDS else text

            # по идее, это обрабатывается в классе бота, и не имеет смысла тут, но пусть будет
            type_com = 'ask_bot' if type_com != text and cls.qu_ans_test(text) else type_com
            if type_com in ['/stat', '/erease', "/gen"]:
                (cls.priority_rec_db if type_com in HIGH_PRIORITY_SIGNAL
                 else cls.secondary_res_db).put((type_com, [chat_id,
                                                            [callback_func, args, kwargs]]))
            elif type_com in ["ask_bot"]:
                cls.question_ans(callback_func, *args, **kwargs)  # сразу отправляем в вк
            elif type_com in ['new_words']:
                # [(type_rec: str, [id_chat: int, [{start_w: {val: count, ...}, ...},
                #                                  {word: {val: count, ...}, ...}]]), ...]
                (cls.priority_rec_db if type_com in HIGH_PRIORITY_SIGNAL
                 else cls.secondary_res_db).put((type_com, [chat_id, cls.edit_msd_text(text)]))

    @classmethod
    def question_ans(cls, callback_func, *args, **kwargs):
        cls.sending_msg(('func', [callback_func,
                                  [cls.random_answ()] + args,
                                  kwargs]))

    @classmethod
    def edit_msd_text(cls, text):
        if type(text) == list:
            text = ' '.join(text)
        _dict = dict()
        start_w_dict = dict()
        for part in (part.split() for part in
                           iter(re_split(r'[.!?]()', re_sub(r'[^.,!:;? ]()[.,!:?;]', ' ', text.lower())))
                     if len(part.split()) > 1):
            for i in range(1, len(part) - 1):
                _dict[part[i]] = _dict.get(part[i], Counter()) + Counter({part[i + 1]: 1})
            start_w_dict[part[0]] = start_w_dict.get(part[0], Counter()) + Counter({part[1]: 1})
            _dict[part[-1]] = start_w_dict.get(part[-1], Counter())
        return [start_w_dict, _dict]