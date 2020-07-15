from import_libs import *


class VkBot():
    vk_session = None
    run = False
    msg = dict()
    counter_msg = 0

    @classmethod
    def start(cls):
        cls.run = True
        cls.vk_session = VkApi(token=cfg.get("vk", "token"))
        longpoll = VkBotLongPoll(cls.vk_session, group_id=cfg.get("vk", "group"))

        cls.listen_events(longpoll)

    @classmethod
    def listen_events(cls, longpoll):
        while cls.run:
            try:
                for ev in longpoll.listen():
                    cls.processing_event(ev)
            except Exception as e:
                print("произошла неизвестная ошибка", e)

    @classmethod
    def processing_event(cls, event):
        print('something event', event)
        if event.type == VkBotEventType.MESSAGE_NEW:
            print('новое сообщение')
            cls.msg[cls.counter_msg] = WorkWithMessenges.processing_msg(event,
                                                                        key=cls.counter_msg,
                                                                        d=cls.msg)
            cls.counter_msg += 1
            print(cls.msg[0].counter)


class WorkWithMessenges():
    def __init__(self, event, key=None, d=None):
        # d - словарь, в котором хранятся обрабатываемые сообщения; key - ключ словаря
        if event.type == VkBotEventType.MESSAGE_NEW:
            self.processing_msg(event, cls=self, key=key, d=d)

    @staticmethod
    def processing_msg(event, cls=None, key=None, d=None):
        text = event.object.text
        print('пришло сообщение с текстом:', text)
        if key and d:

        if cls:
            print('deeeeeeeeeeel')
            del cls
