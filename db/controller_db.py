from db.models import *
from random import randint
from collections import Counter


class DbControl():
    calls_q_pr = None  # очередь, события в которой требуют ответа (приоритетная)
    calls_q_sec = None  # очередь, события в которой не требуют ответа (второстепенная)
    result_q = None  # очередь, в которую отправляется результат запроса из БД
    run = False

    @classmethod
    def start(cls, **kwargs):
        try:
            cls.calls_q_pr = kwargs["priority_rec_db"]
            cls.calls_q_sec = kwargs["secondary_res_db"]
            cls.result_q = kwargs['sending_msg']
            cls.run = True
            cls.working(**kwargs)
        except Exception as e:
            print('произошла какая-то ошибка в классе', cls.__name__, ":", e)
        return cls.start

    @classmethod
    def working(cls, **kwargs):
        while cls.run:
            if not cls.calls_q_pr.empty() or not cls.calls_q_sec.empty():
                cls.calls_processing(**kwargs)
            else:
                cls.run = False

    @classmethod
    def calls_processing(cls, **kwargs):
        # print("******************************************")
        # если приоритетная очередь пуста, то читаем данные из второстепенной
        type_ev, request = (cls.calls_q_sec.get() if cls.calls_q_pr.empty() else cls.calls_q_pr.get())
        if type_ev == 'new_words':
            # print('&&&&&&&&^^^^^^^^^^^', request)
            cls.new_msg_processing(*request, **kwargs)  # id_chat, text_msg
        elif type_ev == '/gen':
            cls.generate_new_msg(*request, **kwargs)  #id_chat, callback_func, [args], dict(kwargs)

        elif type_ev == '/stat':
            # print('^^^^^^^^^^^&&&&&&&&^^^^^^^^^^^', request)
            cls.get_stat(*request, **kwargs)  #id_chat, callback_func, [args], dict(kwargs)
        elif type_ev == '/erease':
            cls.erease_processing(*request, **kwargs)  #id_chat, callback_func, [args], dict(kwargs)


    @classmethod
    @db_session
    def generate_new_msg(cls, id_chat, rec, *args, **kwargs):
        callback_func, m_args, m_kwargs = rec

        # print('получение /gen из БД')
        if Chat.exists(id=id_chat) and Chat[id_chat].count_words > 0:
            chat_now = Chat[id_chat]
            max_len = randint(1, 50)
            ans = []
            entity = None
            while True:
                if not entity and max_len > 0:
                    print(chat_now.start_words)
                    entity = list(chat_now.start_words)[randint(0, len(chat_now.start_words)-1)]
                    print(entity)
                    if bool(ans) and ans[-1] not in list('.!?'):
                        ans.append('.')
                else:
                    break
                ans.append(entity.word)
                max_len -= 1
                if max_len < -500:
                    break
                print('*********----')
                entity = (None if entity.len_vals < 1 else list(entity.val)[randint(0, len(entity.val) - 1)])
                print('*********----', entity)
        else:
            if not Chat.exists(id=id_chat):
                Chat(id=id_chat)
                #flush()
            ans = 'Я не могу писать, если не знаю слов :c'
        kwargs['sending_msg'].put(('func', [callback_func, [ans] + m_args, m_kwargs]))



    @classmethod
    @db_session
    def new_msg_processing(cls, id_chat, text_msg, *other, **kwargs):
        # print("работает обработка нового сообщения", id_chat, text_msg, *other)
        # text_msg  =  [({start_w: {val: count, ...}, ...} {word: {word_val: count, ...}, ...}), ...]
        if not Chat.exists(id=id_chat):
            Chat(id=id_chat)
            flush()

        chat_now = Chat[id_chat]
        text_msg = ((StartWords, Words, text_msg[0], {'chat': Chat[id_chat]}), (Words, Words, text_msg[1], {}))
        for [entity, target_entity, part, other_params] in text_msg:
            [entity(chat_id=id_chat, word=w,
                    **other_params) for w in part.keys() if not entity.exists(chat_id=id_chat, word=w)]
            flush()
        # print('все новые слова внесены в БД')
        for [entity, target_entity, part, other_params] in text_msg:
            for key, vals in part.items():
                # print('start pr', key, vals)
                w = entity[id_chat, key]
                w.val = arr = set(w.val + [target_entity[id_chat, w_val] for w_val in vals.keys()])
                # print('$$$$')
                w.len_vals = len(arr)
                w.count_vals += sum(vals.values())
                #print(')))))')
                chat_now.count_words += sum(vals.values())
                w.vals_dict = dict(Counter(w.vals_dict) + Counter(vals))
                # print('end pr')
        commit()
        show(StartWords)
        # print('--------------------------------------')



    @classmethod
    @db_session
    def get_stat(cls, id_chat, rec, *args, **kwargs):
        callback_func, m_args, m_kwargs = rec
        # print('получение /stat из БД', args)
        kwargs['sending_msg'].put(('func', (callback_func,
                                            [f'''📝 Количество использованных слов: {Chat[id_chat].count_words}
                                        🔢 ID чата: {id_chat}'''] + list(m_args),
                                   m_kwargs)))


    @classmethod
    @db_session
    def erease_processing(cls, id_chat, rec, *args, **kwargs):
        callback_func, m_args, m_kwargs = rec
        # print('очищение помяти БД')
        try:
            delete(w for w in Words if w.chat_id == id_chat)
            delete(w for w in StartWords if w.chat_id == id_chat)
            Chat[id_chat].delete()
            ans = 'Память была успешно очищена😎'
        except Exception as e:
            print('произошла ошибка при очищении памяти чата', id_chat, ":", e)
            ans = 'При очищении память произошла какая-то ошибка👉🏻👈🏻😅'
        kwargs['sending_msg'].put(['func', [callback_func,
                                   [ans] + m_args,
                                   m_kwargs]])




