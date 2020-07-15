from import_libs import *


class VkBot():
    vk_session = None
    run = False
    msg = dict()
    counter_msg = 0
    pool = None  # пространство с процессами

    @classmethod
    def start(cls, pool=None, lock=None, n_msg=None):
        cls.run = True
        cls.pool = pool
        cls.lock = lock
        cls.vk_session = VkApi(token=cfg.get("vk", "token"))
        longpoll = VkBotLongPoll(cls.vk_session, group_id=cfg.get("vk", "group"))

        cls.listen_events(longpoll, n_msg=n_msg)

    @classmethod
    def listen_events(cls, longpoll, n_msg=None):
        while cls.run:
            try:
                for ev in longpoll.listen():
                    cls.processing_event(ev, n_msg=n_msg)
            except Exception as e:
                print("произошла неизвестная ошибка", e)

    @classmethod
    def processing_event(cls, event, n_msg=None):
        print('something event', event)
        if event.type == VkBotEventType.MESSAGE_NEW:
            print('новое сообщение', type(event.raw), event.raw)
            n_msg.put(event.raw)


class WorkWithMessenges():
    run = False

    @classmethod
    def start(cls, n_msg):  # , n_msg=None
        try:
            cls.run = True
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

    @classmethod
    def new_msg_queue_cheching(cls, n_msg=None):
        if not n_msg.empty():
            cls.processing_msg(n_msg.get())
        else:
            pass
            # cls.run = False

    @staticmethod
    def processing_msg(event):
        print('пришло сообщение с текстом:', event)
