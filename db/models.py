from pony.orm import *

db = Database()


class Words(db.Entity):
    id = PrimaryKey(int, auto=True)
    word = Optional(str)
    key = Set('Words', reverse='val')
    val = Set('Words', reverse='key')
    vals_dict = Optional(Json)  # dict(str, [int])  (ключевое слово: количество повторений)
    len_vals = Optional(int)  # количество ключевых слов
    count_vals = Optional(int)  # кол-во встречающихся слов
    start_wordss = Set('Start_words')


class Chat(db.Entity):
    id = PrimaryKey(int, auto=True)
    count_words = Optional(int)
    start_words = Optional('Start_words')


class Start_words(db.Entity):
    id = PrimaryKey(int, auto=True)
    chat = Optional(Chat)
    words = Set(Words)




if __name__ == '__main__':

    db.bind(provider='sqlite', filename='test.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
    with db_session:
        if not Words.exists(word='привет'):
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

