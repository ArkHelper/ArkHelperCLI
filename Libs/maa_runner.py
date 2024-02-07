import var
from Libs.utils import *
from Libs.process_runner import start_task_process
from Libs.maa_util import update_nav
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.model import Device


import logging
import os
import time
import copy
import multiprocessing
import json


def do_conclusion():
    # TODO: using task running result
    file_name = r'%y-%m-%d-%H-%M-%S.json'
    file_name = var.start_time.strftime(file_name)

    file = var.cli_env / 'conclusion' / file_name

    def _get_conclusion():
        return {
            "msg": 'AkhCLI任务全部完成',
            "startTime": int(var.start_time.timestamp()*1000),
            "endTime": int(time.time()*1000),
            "code": 0,
            "extra": {}
        }

    file.parent.mkdir(exist_ok=True)
    conclusion = _get_conclusion()

    write_json(file, conclusion)


def kill_all_emulators():
    for process in var.global_config['devices']:
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)


def run():
    update_nav()
    # exec_adb_cmd('kill-server')
    # exec_adb_cmd('start-server')
    # kill_all_emulators()

    tasks = [get_full_task(personal_config) for personal_config in var.personal_configs]
    devices = [Device(dev_config) for dev_config in var.global_config['devices']]
    task_statuses: list[list[Device, multiprocessing.Process, dict, dict]] = [[_device, None, None, None] for _device in devices]

    while True:
        ended_dev = []
        for task_status in task_statuses:
            logger = task_status[0].logger

            if task_status[1] != None:
                if not task_status[1].is_alive():
                    logger.debug(f'TaskProcess {task_status[2]["task"]["hash"]} ended, clearing.')
                    task_status[1] = None
                    task_status[2] = None
                    task_status[3] = None

            if task_status[1] == None:
                logger.debug(f'Process is None, distributing task.')
                def no_task():
                    logger.debug(f'No task to distribute. Ended.')
                    ended_dev.append(task_status[0])
                if tasks:
                    distribute_task = (
                        [task for task in tasks if task.get('device') == task_status[0].alias] or
                        [task for task in tasks if task.get('device') is None] or
                        [None]
                    )[0]

                    if distribute_task:
                        tasks.remove(distribute_task)
                        process_static_params = {
                            "task": distribute_task,
                            "device": task_status[0]
                        }
                        process_shared_status = multiprocessing.Manager().dict()
                        process = multiprocessing.Process(target=start_task_process, args=(process_static_params, process_shared_status, ))

                        task_status[1] = process
                        task_status[2] = process_static_params
                        task_status[3] = process_shared_status

                        logger.debug(f'Ready to start a task process(task={distribute_task["hash"]}).')
                        process.start()
                    else:
                        no_task()
                else:
                    no_task()

        if len(ended_dev) == len(devices):
            logger.debug(f'All devices ended. Exiting.')
            break
        else:
            time.sleep(2)

    kill_all_emulators()
    do_conclusion()


def get_full_task(config):
    final_maatasks: list = []
    overrides = config['override']
    server = ''
    for default_task in var.default_personal_config:
        default_task: dict

        final_task_config = copy.deepcopy(default_task['task_config'])
        final_task_name = copy.deepcopy(default_task['task_name'])

        preference_task_config = \
            (
                [override['task_config'] for override in overrides if override['task_name'] == final_task_name] or
                [{}]
            )[0]

        def update():
            final_task_config.update(preference_task_config)

        def append():
            if final_task_config.get('enable', True):
                final_maatasks.append({
                    'task_name': final_task_name,
                    'task_config': final_task_config
                })

        if final_task_name == 'StartUp':
            update()
            append()

            server = final_task_config.get('client_type', 'Official')
        elif final_task_name == 'Fight':
            preference_checkpoint = preference_task_config.get('stage')

            if preference_checkpoint and type(preference_checkpoint) is dict:
                checkpoints_in_limit_list = [cp for cp in preference_checkpoint if cp.rsplit('-', 1)[0] in arknights_checkpoint_opening_time]
                checkpoints_outof_limit_list = [cp for cp in preference_checkpoint if not cp.rsplit('-', 1)[0] in arknights_checkpoint_opening_time]

                for checkpoint in checkpoints_in_limit_list:
                    opening_time = arknights_checkpoint_opening_time[checkpoint.rsplit('-', 1)[0]]

                    if get_game_week(server) not in opening_time:
                        preference_checkpoint.pop(checkpoint)
                        continue

                    rate_standard_coefficient = len(opening_time)
                    preference_checkpoint[checkpoint] /= rate_standard_coefficient  # 平衡概率

                for checkpoint in checkpoints_outof_limit_list:
                    preference_checkpoint[checkpoint] /= 7  # 平衡概率

                preference_task_config['stage'] = random_choice_with_weights(preference_checkpoint)

            update()
            append()
        else:
            update()
            append()

    task = {
        'task': final_maatasks,
        'device': config.get('device', None),
        'server': server
    }
    task_hash = generate_hash(json.dumps(task, ensure_ascii=False))
    logging.debug(f'Generated hash {task_hash} for task: {task}')
    task['hash'] = task_hash
    return task
