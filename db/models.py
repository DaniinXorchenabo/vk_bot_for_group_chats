from pony.orm import *


db = Database()


class Words(db.Entity):
    id = PrimaryKey(int, auto=True)
    word = Optional(str, default="")
    key = Set('Words', reverse='val')
    val = Set('Words', reverse='key')
    vals_dict = Optional(Json)  # dict(str, [int])  (ключевое слово: количество повторений)
    len_vals = Optional(int, default=0)  # количество ключевых слов
    count_vals = Optional(int, default=0)  # кол-во встречающихся слов
    start_wordss = Set('Start_words')


class Chat(db.Entity):
    id = PrimaryKey(int, auto=True)
    count_words = Optional(int, default=0)
    start_words = Optional('Start_words')
    

class Start_words(db.Entity):
    id = PrimaryKey(int, auto=True)
    chat = Optional(Chat)
    words = Set(Words)


def is_DB_created():
    from os import getcwd, chdir
    from os.path import (
        join as os_join,
        isfile
    )
    from settings.config import cfg


    path = getcwd()
    if path[-3:] in ['\db', '\\db', '/db']:
        chdir(path[:-2])  # изменяем текущую директорию до директории проекта
    path = getcwd()
    name_db = cfg.get("db", "name")
    if not isfile(os_join(path, "db", name_db)):
        db.bind(provider=cfg.get("db", "type"), filename=name_db, create_db=True)
        print('create db')
    else:
        db.bind(provider=cfg.get("db", "type"), filename=name_db)


is_DB_created()
db.generate_mapping(create_tables=True)
if __name__ == '__main__':
    pass







    '''
    with db_session:
        if False:
            start_w = Words(word='привет')
            commit()
            second_w1 = Words(word='Вова', key=start_w)
            second_w2 = Words(word='Аня', key=start_w)
            second_w3 = Words(word='Соня', key=start_w)
            commit()
            th_1w1 = Words(word='пам пам пам', key=second_w1)
            th_1w2 = Words(word='пам пам пам1', key=second_w1)
            th_1w3 = Words(word='пам пам пам2', key=second_w1)

            th_2w1 = Words(word='хорошо выглядишь', key=second_w2)
            th_2w2 = Words(word='плохо выглядишь', key=second_w2)
            commit()
    with db_session:
        data = Words.get(word='привет')
        #print(data.word, [i.word for i in data.key], [f'{str(i.word)} ' + str([j.word for j in i.key]) + ' '+ str([str(j.word) +' !!' + str([c.word for c in j.key]) + " !!" for j in i.val]) for i in data.val])
    '''
