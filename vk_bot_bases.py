from import_libs import *

class VkBotBase():
    ANSWERS = ['Да', 'Нет', 'Не знаю', 'Сложно ответить',
               'Даже мудрецы не знают ответа на этот вопрос',
               'Не важно. Съешь яблоко!', 'А почему ты спрашиваешь?',
               'Скорее нет, чем да', 'Скорее да, чем нет',
               'Что?', 'Ты пятый раз это спрашиваешь!']

    ALL_COMMANDS = ['/stat', '/erease', "/gen", "/kw", "/no_kw", '/help']
    DBLESS_COMMANDS = ["/kw", "/no_kw", '/help', '/ask_bot']  # команды, не требующие участия БД
    TEXT_HELP_COMMANDS = ''
    vk_session = None
    run = False

    @classmethod
    def start(cls, *args, **kwargs):
        try:
            cls.run = True
            cls.vk_session = VkApi(token=cfg.get("vk", "token"))
            cls.child_class_start(*args, **kwargs)
        except Exception as e:
            print("произошла неизвестная ошибка в классе", cls.__name__, ':', e)
        return cls.start

    # должен быть переопределен дочерним классом
    @classmethod
    def child_class_start(cls, *args, **kwargs):
        pass

    @staticmethod  # запрос на включение потока с обработкой сообщений
    def processong_msg_class_start(cls, obj, **kwargs):
        kwargs['turn_on_proc'].put((obj, dict()))  # {'kwds': 'kwargs'}
        # print('запуск WorkWithMessenges.start')

    @staticmethod
    def send_q(cls, type_m, other: list, *args, **kwargs):
        kwargs['sending_msg'].put((type_m, other))

    @staticmethod
    def qu_ans_test(text):
        return text[:4] in ['бот,', "Бот,"] and text[-1] == '?'

    random_answ = lambda: VkBotBase.ANSWERS[randint(0, len(VkBotBase.ANSWERS) - 1)]