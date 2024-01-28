import json
from multiprocessing import Process
import subprocess
from xml.dom import IndexSizeErr
from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_tostr, load_res_for_asst, update_nav
from Libs.utils import kill_processes_by_name, random_choice_with_weights, read_config, read_json, read_yaml, arknights_checkpoint_opening_time, get_game_week, arknights_package_name, write_json
import var
from Libs.process_runner import start_process

import logging
import os
import time
import copy
import multiprocessing


def do_conclusion():
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
        logging.info(f'trying to kill {process}')
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)


def run():
    # dev.exec_adb('start-server')
    update_nav()
    kill_all_emulators()

    tasks = multiprocessing.Manager().list()
    result = multiprocessing.Manager().list()
    shared_status = multiprocessing.Manager().dict()
    shared_status['tasks'] = tasks
    shared_status['result'] = result
    for personal_config in var.personal_configs:
        tasks.append(extend_full_tasks(personal_config))

    processes: list[Process] = []
    for index, dev in enumerate(var.global_config['devices']):
        process = multiprocessing.Process(target=start_process, args=(shared_status, {'device': dev, 'pid': index}))
        process.start()
        processes.append(process)

    while any([p.is_alive() for p in processes]):
        time.sleep(2)

    kill_all_emulators()
    do_conclusion()


def extend_full_tasks(config):
    final_tasks: list = []

    overrides = config['override']
    black_task_names = config.get('blacklist', [])
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

        if final_task_name not in black_task_names:
            def update():
                final_task_config.update(preference_task_config)

            def append():
                final_tasks.append({
                    'task_name': final_task_name,
                    'task_config': final_task_config
                })

            # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
            # FIXME:(好像修好了)
            if final_task_name == 'StartUp':
                update()
                append()

                server = final_task_config.get('client_type', 'Official')

                if final_task_config.get('account_name', '') != '' and False:
                    another_startup_task_config = copy.deepcopy(
                        final_task_config)
                    another_startup_task_config['account_name'] = ''
                    final_tasks.append({
                        'task_name': final_task_name,
                        'task_config': another_startup_task_config
                    })
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
        'task': final_tasks,
        'device': config.get('device', None),
        'server': server
    }
    task_hash = hash(json.dumps(task, ensure_ascii=False))
    logging.debug(f'Generated hash {task_hash} for task: {task}')
    task['hash'] = task_hash
    return task
