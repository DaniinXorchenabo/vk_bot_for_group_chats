from work_with_vk import *




if __name__ == '__main__':
    print("Number of cpu : ", cpu_count())
    pool = Pool(processes=processes_count)
    lock = Lock()
    new_msg = Manager().Queue()
    proc_msg = pool.apply_async(WorkWithMessenges.start, args=(new_msg,))
    VkBot.start(pool=pool, lock=lock, n_msg=new_msg)