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

COMANDS = ['/stat', '/erease', "/gen", "/kw", "/no_kw", '/help']


class VkBot():
    """Класс работает в двух потоках, как следствие
    разделен на 2 части.
    В одном потоке:
            прием событий от бота
    В другом потоке:
            отправка сообщений пользователю"""

    DBless_comands = ["/kw", "/no_kw", '/help']  # команды, не требующие участия БД
    vk_session = None
    run = False
    obj_dict = dict()  # dict(id_chat: VkBot)
    TEXT_HELP_COMANDS = ''

    # !!! часть класса, отвечающая за прием события !!!
    @classmethod
    def listen_events(cls, longpoll=None, vk_session=None, **kwargs):
        try:
            print('listen_events vkBot started !')
            cls.obj_dict = None  # для части класса, работающей в этом потоке не используется
            cls.run = True
            if not cls.vk_session:
                cls.vk_session = VkApi(token=cfg.get("vk", "token"))
            longpoll = VkBotLongPoll(cls.vk_session, group_id=cfg.get("vk", "group"))

            while cls.run:
                for ev in longpoll.listen():
                    cls.processing_event(ev, **kwargs)
        except Exception as e:
            print("произошла неизвестная ошибка в классе", cls.__name__, '(listen_events):', e)
        return cls.listen_events

    @classmethod
    def processing_event(cls, event, **kwargs):
        # print('something event', event)
        if event.type == VkBotEventType.MESSAGE_NEW:
            text = event.object.text
            if WorkWithMessenges.qu_ans_test(text):
                cls.send_q('func', [cls.send_msg, [WorkWithMessenges.random_answ()],
                                    cls.generate_answ_dict(event.raw)], **kwargs)
            elif event.object.text in cls.DBless_comands:
                cls.send_q('func', [cls.proc_DBless_msg, [text], event.raw], **kwargs)
            else:
                event_d = dict(event.raw)
                event_d.update({'callback_func': cls.send_msg,
                                "args": [],
                                "kwargs": cls.generate_answ_dict(event_d)})

                kwargs['n_msg'].put(event_d)
                cls.processong_msg_class_start(**kwargs)

    # ==========! work with other classes !==========
    @classmethod  # запрос на включение потока с обработкой сообщений
    def processong_msg_class_start(cls, **kwargs):
        kwargs['turn_on_proc'].put((WorkWithMessenges.start, dict()))  # {'kwds': 'kwargs'}
        # print('запуск WorkWithMessenges.start')

    @classmethod
    def send_q(cls, type_m, other: list, *args, **kwargs):
        kwargs['sending_msg'].put((type_m, other))

    # !!! часть класса, отвечающая за отправку сообщений !!!
    @classmethod
    def start(cls, **kwargs):
        try:
            cls.run = True
            cls.vk_session = VkApi(token=cfg.get("vk", "token"))
            kwargs['turn_on_proc'].put((cls.listen_events, dict()))
            cls.TEXT_HELP_COMANDS = cls.get_help_comand()
            cls.sending_msg_queue_processing(**kwargs)
        except Exception as e:
            print('произошла какая-то ошибка в клсаае', cls.__name__, '(start):', e)
        return cls.start

    # ==========! send msg !==========
    @classmethod
    def sending_msg_queue_processing(cls, **kwargs_f):
        while True:
            if not kwargs_f['sending_msg'].empty():
                print('---------------new msg get!!!!!!!')
                _type, material = kwargs_f['sending_msg'].get()
                if _type == 'func':
                    func, args, kwargs = material
                    if kwargs.get('peer_id', None) and not cls.obj_dict.get(kwargs.get('peer_id')):
                        cls.obj_dict[kwargs.get('peer_id')] = cls()
                    kwargs.pop('callback_func', None)
                    func(*args, **kwargs)
            else:
                sleep(0.1)

    @classmethod
    def send_msg(cls, text, *args, **kwargs):
        msg = cls.generate_answ_dict(cls.constructor_msg(text, **kwargs), func=lambda i: type(i) != dict)
        cls.vk_session.method("messages.send", msg)

    # ==========! обработка сообщений !==========
    @classmethod
    def generate_answ_dict(cls, _dict: dict, func=lambda i: True):
        nested_dict = []
        standart_d = {key: val for key, val in _dict.items()
                      if not (type(val) == dict and nested_dict.append(key)) and key in list_keys and func(val)}
        # print('standart_d', standart_d)
        [standart_d.update(cls.generate_answ_dict(_dict[key])) for key in nested_dict]
        # print('standart_d', standart_d)
        return standart_d

    @classmethod
    def constructor_msg(cls, text, **kwargs):
        if type(text) == list:
            text = ' '.join(text)
        if type(text) != str:
            text = str(text)
        text = re_sub(r'(\s{1,})[.,!:;]', '', text)
        if kwargs.get('peer_id', None) and  cls.obj_dict.get(kwargs.get('peer_id')):
            # характеристики сообщений чата, присущие только ему (к примеру, клавиатура)
            kwargs.update(cls.obj_dict[kwargs['peer_id']].unical_dict)
        kwargs.update({"message": text, 'random_id': randint(1, 2147483647)})
        return kwargs

    #==========! Распределение сообщений по типам для ответа на них (для не требующих контакта с БД) !==========
    @classmethod
    def proc_DBless_msg(cls, msg, *args, **kwargs):
        if msg == '/help':
            cls.send_msg(cls.TEXT_HELP_COMANDS, *args, **kwargs)



    @staticmethod
    def get_help_comand():
        with open('settings/comands.txt', 'r', encoding='utf-8') as f:
            return f.read()

    # ==========! No classmethod !==========
    def __init__(self):
        self.unical_dict = {'keyboard': None}


class WorkWithMessenges():
    run = False
    sending_msg = None
    secondary_res_db = priority_rec_db = None
    qu_ans_test = lambda text: text[:4] in ['бот,', "Бот,"] and text[-1] == '?'
    random_answ = lambda: answers[randint(0, len(answers) - 1)]
    working_with_bd_pros_live = False

    @classmethod
    def work_db_start(cls, **kwargs):
        kwargs['turn_on_proc'].put((DbControl.start, dict()))  # {'kwds': kwargs}

    @classmethod
    def start(cls, *args, **kwargs):  # , n_msg=None
        try:
            print('class', cls.__name__, "started")
            cls.run = True
            cls.working_with_bd_pros_live = False
            cls.sending_msg = kwargs['sending_msg']
            cls.priority_rec_db = kwargs['priority_rec_db']
            cls.secondary_res_db = kwargs['secondary_res_db']
            cls.working_cls(**kwargs)
        except Exception as e:
            print('произошла какая-то ошибка при старте класса', cls.__name__, e)
        return cls.start

    @classmethod
    def working_cls(cls, **kwargs):
        while cls.run:
            try:
                cls.new_msg_queue_cheching(**kwargs)
            except Exception as e:
                print('произошла неизвестная ошибка в', cls.__name__, ":", e)
        print('class', cls.__name__, "end working")

    @classmethod
    def new_msg_queue_cheching(cls, **kwargs):
        if not kwargs['n_msg'].empty():
            cls.processing_msg(kwargs['n_msg'].get(), **kwargs)
        else:
            sleep(0.1)
            #cls.run = False

    @classmethod
    def processing_msg(cls, event, **f_kwargs):
        # print('пришло сообщение с текстом:', event)
        if type(event) == dict:
            text = event['object']['text']
            chat_id = event['object']['peer_id']
            callback_func = event['callback_func']
            args, kwargs = event.pop('args', {}), event.pop('kwargs', {})
            kwargs.update(event)
            type_com = 'new_words' if text not in COMANDS else text

            # по идее, это обрабатывается в классе бота, и не имеет смысла тут, но пусть будет
            type_com = 'ask_bot' if type_com != text and cls.qu_ans_test(text) else type_com
            if type_com in ['/stat', '/erease', "/gen"]:
                (cls.priority_rec_db if type_com in HIGH_PRIORITY_SIGNAL
                 else cls.secondary_res_db).put((type_com, [chat_id,
                                                            [callback_func, args, kwargs]]))
                cls.work_db_start(**f_kwargs)
                # print('сообщение отправлено к бд')
            elif type_com in ["ask_bot"]:
                cls.question_ans(callback_func, *args, **kwargs)  # сразу отправляем в вк
            elif type_com in ['new_words']:
                # [(type_rec: str, [id_chat: int, [{start_w: {val: count, ...}, ...},
                #                                  {word: {val: count, ...}, ...}]]), ...]
                (cls.priority_rec_db if type_com in HIGH_PRIORITY_SIGNAL
                 else cls.secondary_res_db).put((type_com, [chat_id, cls.edit_msd_text(text)]))
                cls.work_db_start(**f_kwargs)
            #     print('сообщение отправлено к бд - 2')
            # print('сообщение обработано и отправлено по очередям')

    @classmethod
    def question_ans(cls, callback_func, *args, **kwargs):
        kwargs['sending_msg'].put(('func', [callback_func,
                                            [cls.random_answ()] + args,
                                            kwargs]))

    @classmethod
    def edit_msd_text(cls, text):
        if type(text) == list:
            text = ' '.join(text)
        _dict = dict()
        start_w_dict = dict()  # #@*`~
        for part in (part.split() for part in
                     iter(re_sub(r'()([.!?\n]{1,})',
                                 r'\1 \2 #@*`~', re_sub(r'([^.,!:;?«» ])()([.,!:?;«»\n]{1,})',
                                                        r'\1 \2 \3',
                                                        text.lower())).split('#@*`~')) if len(part.split()) > 0):
            # print(part)
            if len(part) == 1:
                part += ['.']
            for i in range(1, len(part) - 1):
                _dict[part[i]] = _dict.get(part[i], Counter()) + Counter({part[i + 1]: 1})
            start_w_dict[part[0]] = start_w_dict.get(part[0], Counter()) + Counter({part[1]: 1})
            _dict[part[-1]] = start_w_dict.get(part[-1], Counter())
        print('start_w_dict', start_w_dict)
        print("_dict", _dict)
        return [start_w_dict, _dict]
