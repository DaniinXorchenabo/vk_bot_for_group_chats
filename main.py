


by_ended_process = set()  # список неактивных процессов


def callback_func(*args, **kwargs):
    by_ended_process.add(args[0])
    print("callback_func", str(args[0].__repr__()).split()[2], kwargs)
    print(*[(key, val.empty()) for key, val in kwargs_for_classws.items() if type(val) == type(Manager().Queue())])


def error_callback_func(*args, **kwargs):
    print('---------------------------------')
    print('error_callback_func', )
    print(args)
    print(kwargs)
    print('---------------------------------')


if __name__ == '__main__':
    from work_with_vk import *


    print("Number of cpu : ", cpu_count(), print(ctime()))
    pool = Pool(processes=processes_count)
    new_msg = Manager().Queue()  # [dict(), ...]  тексты сообщений из бота в обработку

    # запросы к БД, которые требуют от бота ответа (выполняются в первую очередь)
    # [(type_rec: str, [ id_chat:int, [callback_func, [args: list], [kwargs: dict]] ]), ...]
    priority_rec_db = Manager().Queue()

    # запросы к БД, которые не требуют ответа (обучение бота) (выполняются, когда есть время)
    # [(type_rec: str, [id_chat: int, [{start_w: {val: count, ...}, ...}, {start_w: {val: count, ...}, ...}]]), ...]
    secondary_res_db = Manager().Queue()

    # тексты сообщений, которые нужно отправить пользователям (беседам)
    sending_msg = Manager().Queue()  # [(type: str, [callback_func, [text, *args], {**kwargs: dict} ]), ...]

    # так как один поток не может включать другой поток, то придется все включать из главного
    turn_on_process_please = Manager().Queue()  # [(work_obj, args: list, kw_param: dict), ...]

    kwargs_for_classws = {'n_msg': new_msg,
                          'sending_msg': sending_msg,
                          'priority_rec_db': priority_rec_db,
                          'secondary_res_db': secondary_res_db,
                          'turn_on_proc': turn_on_process_please, }
    args = []
    data_for_apply_async = {'args': args,
                            "kwds": kwargs_for_classws,
                            'callback': callback_func,
                            'error_callback': error_callback_func}

    res = pool.apply_async(VkBotSending.start, **data_for_apply_async)
    res.ready()
    by_ended_process = {WorkWithMessenges.start, DbControl.start, VkBotListen.start}  # список неактивных процессов
    while True:
        try:
            if not turn_on_process_please.empty():
                obj_call, *args, kw_param = turn_on_process_please.get()
                print('получен запрос на реенкорнацию процесса ', obj_call.__name__, end=' ')
                if obj_call in by_ended_process:
                    _dict = data_for_apply_async.copy()
                    # в пришедшем словаре могут (и должны) встречаться вложенные словари,
                    # приведенный ниже код совмещает вложенные словари
                    # (причем если ключи в них повторяются, то итоговое значение будет записано из нового словаря)
                    [(_dict[key].update(val), kw_param[key].update(_dict[key])) for key, val in kw_param.items()
                     if type(key) == dict and _dict.get(key, None)]
                    # а потом обновляет старый словарь
                    # (можно не опасаться, что мы потеряем данные из вложенных словарей _dict'а,
                    # ибо вложенные словари в _dict и в kw_param - одинаковые)
                    _dict.update(kw_param)
                    # print('сейчас процесс', obj_call, "будет запущен")
                    # print(obj_call, _dict)
                    res_o = pool.apply_async(obj_call, **_dict)
                    # print('процесс', obj_call, "был запущен")
                    by_ended_process.remove(obj_call)
                    res_o.ready()
                    print(': запустили процесс')
                else:
                    print("процесс уже работает")

                    # print('вызов .ready() к процессу', obj_call)
            sleep(0.1)
            # if not sending_msg.empty():
            #     _type, material = sending_msg.get()
            #     if _type == 'func':
            #         func, args, kwargs = material
            #         func(*args, **kwargs)

        except PermissionError as e:
            print('в главном процессе произошло PermissionError', e)
