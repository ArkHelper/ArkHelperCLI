import var
from Libs.utils import *
from Libs.model import Device
from Libs.process_runner import start_task_process
from Libs.maa_util import update_nav
from Libs.task_planner import *


import logging
import time
import copy
import multiprocessing


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


def run():
    update_nav()
    # exec_adb_cmd('kill-server')
    # exec_adb_cmd('start-server')
    # kill_all_emulators()

    [var.tasks.append(get_full_task(personal_config)) for personal_config in var.personal_configs]
    devices = [Device(dev_config) for dev_config in var.global_config['devices']]
    task_statuses: list[list[Device, multiprocessing.Process, dict, dict]] = [[_device, None, None, None] for _device in devices]

    while True:
        ended_dev = []
        for task_status in task_statuses:
            logger = task_status[0].logger

            if task_status[1] != None:
                if not task_status[1].is_alive():
                    logger.debug(f'TaskProcess {task_status[2]["task"]["hash"]} ended, ready to clear.')
                    task_status[1] = None
                    task_status[2] = None
                    task_status[3] = None

            if task_status[1] == None:
                logger.debug(f'Process is None, ready to distribute task.')

                def no_task():
                    logger.debug(f'No task to distribute. Ended.')
                    task_status[0].kill()
                    ended_dev.append(task_status[0])
                if var.tasks:
                    distribute_task = (
                        [task for task in var.tasks if task.get('device') == task_status[0].alias] or
                        [task for task in var.tasks if task.get('device') is None] or
                        [None]
                    )[0]

                    if distribute_task:
                        var.tasks.remove(distribute_task)
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
            logging.debug(f'All devices ended. Ready to exit.')
            break
        else:
            time.sleep(2)

    do_conclusion()


def get_full_task(config):
    final_maatasks: list = []
    overrides = config['override']
    server = ''
    account_name = ''
    for default_task in var.default_personal_config:
        default_task: dict

        final_task_config = copy.deepcopy(default_task['task_config'])
        final_task_name = copy.deepcopy(default_task['task_name'])

        preference_task_config = \
            (
                [override['task_config'] for override in overrides if override['task_name'] == final_task_name] or
                [{}]
            )[0]

        def update_and_match_case():
            nonlocal final_task_config
            final_task_config.update(preference_task_config)

            def get_config(key):
                nonlocal final_task_config
                config = final_task_config[key]

                def time_between(time_start, time_end):
                    current_time = datetime.now().strftime("%H:%M")
                    start_time_obj = datetime.strptime(time_start, "%H:%M")
                    end_time_obj = datetime.strptime(time_end, "%H:%M")
                    current_time_obj = datetime.strptime(current_time, "%H:%M")
                    return start_time_obj <= current_time_obj <= end_time_obj

                def date_between(date_start, date_end):
                    current_date = datetime.now().strftime("%Y/%m/%d")
                    start_date_obj = datetime.strptime(date_start, "%Y/%m/%d")
                    end_date_obj = datetime.strptime(date_end, "%Y/%m/%d")
                    current_date_obj = datetime.strptime(current_date, "%Y/%m/%d")
                    return start_date_obj <= current_date_obj <= end_date_obj

                def datetime_between(datetime_start, datetime_end):
                    current_datetime = datetime.now()
                    start_datetime_obj = datetime.strptime(datetime_start, "%Y/%m/%d-%H:%M:%S")
                    end_datetime_obj = datetime.strptime(datetime_end, "%Y/%m/%d-%H:%M:%S")
                    return start_datetime_obj <= current_datetime <= end_datetime_obj

                AM = in_game_time(datetime.now(), server).hour < 12  # in gametime
                # excuted_time_in_cur_gameday =

                if type(config) == list:
                    try:
                        for case in config:
                            case_condition = case.get('condition', 'True')
                            case_config = case['config']
                            if eval(case_condition):
                                return case_config
                    except:
                        return config
                else:
                    return config
            final_task_config = {key: get_config(key) for key in final_task_config}
            pass

        def append():
            if final_task_config.get('enable', True):
                final_maatasks.append({
                    'task_name': final_task_name,
                    'task_config': final_task_config
                })

        update_and_match_case()
        if final_task_name == 'StartUp':
            server = final_task_config.get('client_type', 'Official')
            account_name = final_task_config.get('account_name', '')
        elif final_task_name == 'Fight':
            stage = final_task_config.get('stage')
            if stage and type(stage) == dict:
                final_task_config['stage'] = choice_stage(server, stage)
        else:
            pass
        append()

    hash = f"{config.get('device', '')}{server}{account_name}"
    if (index := len([t for t in var.tasks if t['hash'] == hash])) != 0:
        hash += f"_{index}"

    task = {
        'hash': hash,
        'task': final_maatasks,
        'device': config.get('device', None),
        'server': server,
        'account_name': account_name
    }
    logging.debug(f'Initialization ended for task {hash}.')
    return task
