import os
import math
import time
import psutil
import asyncio

from tqdm import tqdm
from multiprocessing import Process, Queue, Semaphore
from iqdb_parser import search_iqdb
from file_processing import move_same_name
from config import valid_extensions



RUNNING_PROCESSES = []
check_status = False
print_task, sort_task = None, None

def sub_processing_main(filename, sem, path_input, path_output, path_dict, is_sep_chars, is_dl_images, result_queue, path_error):
    sem.acquire()
    try:
        res = search_iqdb(filename, path_input, path_output, path_dict, is_sep_chars, is_dl_images)
        result_queue.put([res])
    except Exception:
        res = [f'Error: {filename}', os.path.join(path_input, filename), os.path.join(path_error, filename)]
        result_queue.put([res])
    finally:
        sem.release()
        
      
async def sort_main(path_input, path_output, path_dict, is_sep_chars, is_dl_images, parent): 
    global check_status, print_task, sort_task
    sem = Semaphore(int(os.cpu_count() / 2))
    optimal_subprocesses = 12
    filenames_list = [[] for _ in range(math.ceil(len(os.listdir(path_input)) / optimal_subprocesses))]
    result_queue = Queue()
    pb_counter_max = 0 
    
    for filename in tqdm(os.listdir(path_input), desc='Files'):
        if filename.lower().endswith(valid_extensions) and os.path.getsize(f'{path_input}\\{filename}') > 1:
            pb_counter_max += 1
            for elem_list in filenames_list:
                indx = filenames_list.index(elem_list)
                if len(elem_list) < optimal_subprocesses:
                    filenames_list[indx].append(filename)
                    break
    print_task = asyncio.create_task(print_result(result_queue, pb_counter_max, parent))
    sort_task = asyncio.create_task(sort_async(filenames_list, sem, path_input, path_output, path_dict, is_sep_chars, is_dl_images, result_queue, parent.path_error))
    try:
        await asyncio.gather(print_task, sort_task)
    except asyncio.CancelledError:
        pass
    check_status = True
    
async def sort_async(filenames_list, sem, path_input, path_output, path_dict, is_sep_chars, is_dl_images, result_queue, path_error):
    process_life_timer = {}
    to_remove = []
    for element in tqdm(filenames_list, desc='Iteration'):
            curr_p = []
            to_remove = []

            for filename in element:
                p = Process(target=sub_processing_main, args=(filename, sem, path_input, path_output, path_dict, is_sep_chars, is_dl_images, result_queue, path_error))
                RUNNING_PROCESSES.append(p)
                curr_p.append(p)

            if curr_p:
                for p in curr_p:
                    p.start()
                    process_life_timer[p] = time.time()

            while curr_p:
                to_remove.clear()
                for p in curr_p:
                    if p.is_alive():
                        if time.time() - process_life_timer[p] > 60:
                            terminate_child_process(p)
                            p.join(timeout=1)
                            if p.is_alive():
                                p.terminate()
                            to_remove.append(p)
                            print(f'PROCESS TERMINATED: {p}')
                    else:
                        to_remove.append(p)
                        
                for p in to_remove:
                    curr_p.remove(p)
                    del process_life_timer[p]
                await asyncio.sleep(0.25)
                
                
async def print_result(result_queue, pb_counter_max, parent):
    counter = 0
    img_to_mv = []
    while not check_status:
        while not result_queue.empty():
                    test_obj = result_queue.get_nowait()
                    for elem in test_obj:
                        parent.update_text(elem[0], pb_counter_max)
                        counter += 1
                        #print(f"{counter}) {elem[0]}")                 
                        if elem[1] is not None and elem[2] is not None:
                            img_to_mv.append([elem[1], elem[2]])
        if len(img_to_mv) > 0:
            for element in img_to_mv:
                move_same_name(element[0], element[1])
            img_to_mv.clear()
        await asyncio.sleep(0.25)


def terminate_child_process(process):
    try:
        children = psutil.Process(process.pid).children(recursive=True)
        for child in children:
            child.terminate()
        psutil.wait_procs(children, timeout=1)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass


def stop_sort():
    global RUNNING_PROCESSES, print_task, sort_task
    print_task.cancel() if print_task is not None else None
    sort_task.cancel() if sort_task is not None else None

    while any(p.is_alive() for p in RUNNING_PROCESSES):
        for p in RUNNING_PROCESSES:
            if p.is_alive():
                terminate_child_process(p)
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
    



