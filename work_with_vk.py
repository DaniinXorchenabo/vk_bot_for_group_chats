from import_libs import *


class VkBot():
    vk_session = None
    run = False
    msg = []

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
            cls.msg.append(WorkWithMessenges(event))
            print(cls.msg[0].counter)

class WorkWithMessenges():
    counter = 0
    def __init__(self, event, index=None):
        if event.type == VkBotEventType.MESSAGE_NEW:
            self.processing_msg(event, cls=self)
            WorkWithMessenges.counter += 1
            self.counter = WorkWithMessenges.counter


    @staticmethod
    def processing_msg(event, cls=None):
        text = event.object.text
        print('пришло сообщение с текстом:', text)
        if cls:
            print('deeeeeeeeeeel')
            del cls




