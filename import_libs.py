from settings.config import cfg
from vk_api import VkApi
from vk_api.bot_longpoll import (
    VkBotLongPoll,
    VkBotEvent,
    VkBotEventType
)
from multiprocessing import Pool, Queue, cpu_count, Lock
from time import sleep
import multiprocessing as mp


processes_count = cpu_count()




def ffff(n_msg, text='none text'):
    n_msg.put(text)
    sleep(0.1)