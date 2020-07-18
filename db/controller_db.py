from db.models import *
from random import randint
from collections import Counter


class DbControl():
    calls_q_pr = None  # очередь, события в которой требуют ответа (приоритетная)
    calls_q_sec = None  # очередь, события в которой не требуют ответа (второстепенная)
    result_q = None  # очередь, в которую отправляется результат запроса из БД
    run = False

    @classmethod
    def start(cls, calls_q_pr, calls_q_sec, result_q):
        cls.calls_q_pr = calls_q_pr
        cls.calls_q_sec = calls_q_sec
        cls.result_q = result_q
        cls.run = True
        cls.working()

    @classmethod
    def working(cls):
        while cls.run:
            if not cls.calls_q_pr.empty() or not cls.calls_q_sec.empty():
                cls.calls_processing()
            else:
                cls.run = False

    @classmethod
    def calls_processing(cls):
        # если приоритетная очередь пуста, то читаем данные из второстепенной
        type_ev, request = (cls.calls_q_sec.get() if cls.calls_q_pr.empty() else cls.calls_q_pr.get())
        if type_ev == 'new_words':
            cls.new_msg_processing(*request)  # id_chat, text_msg
        elif type_ev == '/gen':
            cls.generate_new_msg(*request)  #id_chat, callback_func, [args], dict(kwargs)
        elif type_ev == '/stat':
            cls.get_stat(*request)  #id_chat, callback_func, [args], dict(kwargs)
        elif type_ev == '/erease':
            cls.erease_processing(*request)  #id_chat, callback_func, [args], dict(kwargs)

    @db_session
    @classmethod
    def generate_new_msg(cls, id_chat, callback_func, args, kwargs):
        if Chat.exists(id=id_chat) and Chat[id_chat].count_words > 0:
            chat_now = Chat[id_chat]
            max_len = randint(1, 50)
            ans = []
            entity = None
            while True:
                if not entity and max_len > 0:
                    entity = chat_now.start_words[randint(0, len(chat_now.start_words)-1)]
                    if entity.word not in '.!?':
                        ans.append('.')
                else:
                    break
                ans.append(entity.word)
                max_len -= 1
                if max_len < -500:
                    break
                entity = (None if entity.len_vals < 1 else entity.words[randint(0, entity.len_vals - 1)])
        else:
            if not Chat.exists(id=id_chat):
                Chat(id=id_chat)
                #flush()
            ans = 'Я не могу писать, если не знаю слов :c'
        cls.result_q.put(['func', [callback_func, [ans] + args, kwargs]])


    @db_session
    @classmethod
    def new_msg_processing(cls, id_chat, text_msg: list):
        # text_msg  =  [({start_w: {val: count, ...}, ...} {word: {word_val: count, ...}, ...}), ...]
        if not Chat.exists(id=id_chat):
            Chat(id=id_chat)
            flush()

        chat_now = Chat[id_chat]
        text_msg = ((StartWords, text_msg[0], {'chat': Chat[id_chat]}), (Words, text_msg[1], {}))
        for [entity, part, other_params] in text_msg:
            chat_now.count_words += 1 + len(part)
            [entity(chat_id=id_chat, word=w,
                    **other_params) for w in part.keys() if not entity.exists(chat_id=id_chat, word=w)]
            flush()
            for key, vals in part.items():
                w = entity[id_chat, key]
                w.val = arr = set(w.val + [entity[id_chat, w_val] for w_val in vals.keys()])
                w.len_vals = len(arr)
                w.count_vals += sum(vals.values())
                w.vals_dict = Counter(w.vals_dict) + w.vals_dict(vals)
        commit()
        show(StartWords)
        print('--------------------------------------')
        show(Words)


    @db_session
    @classmethod
    def get_stat(cls, id_chat, callback_func, args, kwargs):
        cls.result_q.put(['func', [callback_func,
                                   [f'''📝 Количество использованных слов: {Chat[id_chat].count_words}
                                        🔢 ID чата: {id_chat}'''] + args,
                                   kwargs]])

    @db_session
    @classmethod
    def erease_processing(cls, id_chat, callback_func, args, kwargs):
        try:
            delete(w for w in Words if w.chat_id == id_chat)
            delete(w for w in StartWords if w.chat_id == id_chat)
            Chat[id_chat].delete()
            ans = 'Память была успешно очищена😎'
        except Exception as e:
            print('произошла ошибка при очищении памяти чата', id_chat, ":", e)
            ans = 'При очищении память произошла какая-то ошибка👉🏻👈🏻😅'
        cls.result_q.put(['func', [callback_func,
                                   [ans] + args,
                                   kwargs]])




