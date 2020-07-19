from settings.config import cfg
from vk_api import VkApi
from vk_api.bot_longpoll import (
    VkBotLongPoll,
    VkBotEvent,
    VkBotEventType
)
from multiprocessing import Pool, Queue, cpu_count, Lock, Manager
from time import sleep, ctime
import multiprocessing as mp
from random import randint
from collections import defaultdict
from collections import Counter
from  re import (
    sub as re_sub,
    split as re_split
)
from  multiprocessing import AuthenticationError

processes_count = cpu_count()

import nltk
#nltk.download('punkt')
import pymorphy2

# probability score threshold
prob_thresh = 0.4

morph = pymorphy2.MorphAnalyzer()

text = """
0989189960. Привет вам от Светланы. Ура
Привіт усім, Микола з Київа.
А я из Мюнхена, звать меня Макс.
Андрея не забудьте.
Наталію також!
Надія.
Даниіл. Вітання від Даниіла. Иван Родина Москва Калуга Сочи Брест Волга
""".lower()
# print(re_sub(r'([^.,!:;?«» ])()([.,!:?;«»\n]{1,})', r'\1 \2 \3#@*`~', text).split('#@*`~'))  # [^.,!:;?«» ]
#print(re_split(r'[.,!:?;«»\n](\s)', text))  # [^.,!:;?«» ]






# print(morph.parse("Иван")[0].tag)
# print(morph.parse("Брест")[0].tag)
#
# for word in nltk.word_tokenize(text):
#
#     if bool(list(filter(lambda p: p.score > prob_thresh and ('Name' in p.tag or 'Sgtm' in p.tag or "Geox" in p.tag), morph.parse(word)))):
#         print(word)
#     # print('{:<12}\t({:>12})\tscore:\t{:0.3}'.format(word, p.normal_form, p.score))
