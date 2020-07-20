from import_libs import *
from db.controller_db import *
from vk_bot_bases import *

list_keys = ['user_id', "random_id", "peer_id", "domain",
             "chat_id", "user_ids", "message", "lat", "long",
             "attachment", "reply_to", "forward_messages",
             "sticker_id", "group_id", "keyboard", "payload",
             "dont_parse_links", "disable_mentions", "intent",
             "subscribe_id"]


class VkBotListen(VkBotBase):
    """Класс работает в двух потоках, как следствие
    разделен на 2 части.
    В одном потоке:
            прием событий от бота
    В другом потоке:
            отправка сообщений пользователю"""

    # !!! часть класса, отвечающая за прием события !!!
    # @classmethod
    # def start(cls, *args, **kwargs):
    #     print(kwargs)
    #     return super().start_base(cls.child_class_start, *args, **kwargs)

    @classmethod
    def child_class_start(cls, *args, **kwargs):
        longpoll = VkBotLongPoll(cls.vk_session, group_id=cfg.get("vk", "group"))
        cls.listen_events(longpoll=longpoll, **kwargs)

    @classmethod
    def listen_events(cls, longpoll=None, **kwargs):
        while cls.run:
            for ev in longpoll.listen():
                cls.processing_event(ev, **kwargs)

    @classmethod
    def processing_event(cls, event, **kwargs):
        if event.type == VkBotEventType.MESSAGE_NEW:
            text = event.object.text
            if event.object.text in cls.DBLESS_COMMANDS:
                cls.send_q('func', [VkBotSending.proc_DBless_msg, [text], event.raw], **kwargs)
            elif cls.qu_ans_test(text):
                cls.send_q('func', [VkBotSending.proc_DBless_msg, ['/ask_bot'], event.raw], **kwargs)
            else:
                event_d = dict(event.raw)
                event_d.update({'callback_func': VkBotSending.send_msg, "args": [], "kwargs": event_d})
                kwargs['n_msg'].put(event_d)
                cls.processong_msg_class_start(WorkWithMessenges.start, **kwargs)


class VkBotSending(VkBotBase):
    obj_dict = dict()  # dict(id_chat: VkBotSending)


    # @classmethod
    # def start(cls, *args, **kwargs):
    #     return super().start_base(cls.child_class_start, *args, **kwargs)

    @classmethod
    def child_class_start(cls, *args, **kwds_f):
        kwds_f['turn_on_proc'].put((VkBotListen.start, dict()))
        cls.TEXT_HELP_COMMANDS = cls.get_help_command()
        cls.sending_msg_queue_processing(**kwds_f)

    # ==========! send msg !==========
    @classmethod
    def sending_msg_queue_processing(cls, **kwds_f):
        while True:
            if not kwds_f['sending_msg'].empty():
                _type, material = kwds_f['sending_msg'].get()
                if _type == 'func':
                    func, args, kwargs = material
                    if kwargs.get('peer_id', None) and not cls.obj_dict.get(kwargs.get('peer_id')):
                        cls.obj_dict[kwargs.get('peer_id')] = cls()
                    kwargs.pop('callback_func', None)
                    func(*args, **kwargs)
            else:
                sleep(0.1)

    @staticmethod
    def get_help_command():
        with open('settings/commands.txt', 'r', encoding='utf-8') as f:
            return f.read()

    @classmethod
    def send_msg(cls, text, *args, **kwargs):
        msg = cls.gen_answ_dict(cls.constructor_msg(text, **kwargs), func=lambda i: type(i) != dict)
        cls.vk_session.method("messages.send", msg)

    # ==========! обработка сообщений !==========
    @classmethod
    def gen_answ_dict(cls, _dict: dict, func=lambda i: True):
        nested_dict = []
        standart_d = {key: val for key, val in _dict.items()
                      if not (type(val) == dict and nested_dict.append(key)) and key in list_keys and func(val)}
        [standart_d.update(cls.gen_answ_dict(_dict[key])) for key in nested_dict]
        return standart_d

    @classmethod
    def constructor_msg(cls, text, **kwargs):
        if type(text) == list:
            text = ' '.join(text)
        if type(text) != str:
            text = str(text)
        text = re_sub(r'(\s{1,})[.,!:;]', '', text)
        if kwargs.get('peer_id', None) and cls.obj_dict.get(kwargs.get('peer_id')):
            # характеристики сообщений чата, присущие только ему (к примеру, клавиатура)
            kwargs.update(cls.obj_dict[kwargs['peer_id']].own_dict)
        kwargs.update({"message": text, 'random_id': randint(1, 2147483647)})
        return kwargs

    # ==========! Распределение сообщений по типам для ответа на них (для не требующих контакта с БД) !==========
    @classmethod
    def proc_DBless_msg(cls, msg, *args, **kwargs):
        if msg == '/help':
            cls.send_msg(cls.TEXT_HELP_COMMANDS, *args, **kwargs)

    # ==========! No classmethod !==========
    def __init__(self):
        self.own_dict = {'keyboard': None}


class WorkWithMessenges():
    ALL_COMMANDS = VkBotBase.ALL_COMMANDS
    run = False
    sending_msg = None
    secondary_res_db = priority_rec_db = None
    working_with_bd_pros_live = False

    HIGH_PRIORITY_SIGNAL = ['/stat', '/erease', "/gen", 'ask_bot']
    LOW_PRIORITY_SIGNAL = ["new_words"]

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
            # cls.run = False

    @classmethod
    def processing_msg(cls, event, **f_kwargs):
        if type(event) == dict:
            text = event['object']['text']
            chat_id = event['object']['peer_id']
            callback_func = event['callback_func']
            args, kwargs = event.pop('args', {}), event.pop('kwargs', {})
            kwargs.update(event)
            type_com = 'new_words' if text not in cls.ALL_COMMANDS else text
            if type_com in ['/stat', '/erease', "/gen"]:
                cls.prior_q(type_com, [chat_id, [callback_func, args, kwargs]], **f_kwargs)
            elif type_com in ['new_words']:
                cls.prior_q(type_com, [chat_id, cls.edit_msd_text(text)], **f_kwargs)

    @classmethod
    def edit_msd_text(cls, text):
        if type(text) == list:
            text = ' '.join(text)
        _dict = dict()
        start_w_dict = dict()
        for part in (part.split() for part in
                     iter(re_sub(r'()([.!?\n]{1,})',
                                 r'\1 \2 #@*`~', re_sub(r'([^.,!:;?«» ])()([.,!:?;«»\n]{1,})', r'\1 \2 \3',
                                                        text.lower())).split('#@*`~')) if len(part.split()) > 0):
            if len(part) == 1:
                part += ['.']
            for i in range(1, len(part) - 1):
                _dict[part[i]] = _dict.get(part[i], Counter()) + Counter({part[i + 1]: 1})
            start_w_dict[part[0]] = start_w_dict.get(part[0], Counter()) + Counter({part[1]: 1})
            _dict[part[-1]] = start_w_dict.get(part[-1], Counter())
        return [start_w_dict, _dict]

    # выбор очереди по приоритету
    @classmethod
    def change_pr_q(cls, type_com, **kwgs_f):
        return (kwgs_f['priority_rec_db'] if type_com in cls.HIGH_PRIORITY_SIGNAL
                else kwgs_f['secondary_res_db'])

    @classmethod
    def prior_q(cls, type_com, content, **kwgs_f):
        cls.change_pr_q(type_com, **kwgs_f).put((type_com, content))
        cls.work_db_start(**kwgs_f)
        # secondary_res_db
        # [(type_rec: str, [id_chat: int, [{start_w: {val: count, ...}, ...},
        #                                  {word: {val: count, ...}, ...}]]), ...]
