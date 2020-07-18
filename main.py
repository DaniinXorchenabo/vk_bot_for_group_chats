from work_with_vk import *




if __name__ == '__main__':
    print("Number of cpu : ", cpu_count())
    pool = Pool(processes=processes_count)
    lock = Lock()
    new_msg = Manager().Queue()  # [dict(), ...]  тексты сообщений из бота в обработку

    # запросы к БД, которые требуют от бота ответа (выполняются в первую очередь)
    # [(type_rec: str, [ id_chat:int, [callback_func, [args: list], [kwargs: dict]] ]), ...]
    priority_rec_db = Manager().Queue()

    # запросы к БД, которые не требуют ответа (обучение бота) (выполняются, когда есть время)
    # [(type_rec: str, [id_chat: int, [{start_w: {val: count, ...}, ...}, {start_w: {val: count, ...}, ...}]]), ...]
    secondary_res_db = Manager().Queue()

    # тексты сообщений, которые нужно отправить пользователям (беседам)
    sending_msg = Manager().Queue()  # [(type: str, [callback_func, [text, *args], {**kwargs: dict} ]), ...]
    VkBot.start(pool=pool, lock=lock,
                n_msg=new_msg,
                sending_msg=sending_msg,
                priority_rec_db=priority_rec_db,
                secondary_res_db=secondary_res_db
                )
