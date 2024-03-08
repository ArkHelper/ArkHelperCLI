import var
from Libs.utils import *
from Libs.model import *
from Libs.process_runner import start_task_process
from Libs.task_planner import *


import logging
import time
import copy
import multiprocessing
from dataclasses import dataclass
from urllib.parse import quote
from indent_concluder import Item as ConcluderItem


def do_conclusion():
    file_name = r'%y-%m-%d-%H-%M-%S.json'
    file_name = var.start_time.strftime(file_name)

    file = var.cli_env / 'conclusion' / file_name

    def _get_conclusion():
        return {
            'msg': 'AkhCLI任务全部完成',
            'startTime': int(var.start_time.timestamp()*1000),
            'endTime': int(time.time()*1000),
            'code': 0,
            'extra': {}
        }

    file.parent.mkdir(exist_ok=True)
    conclusion = _get_conclusion()

    write_json(file, conclusion)


def get_report(result):
    conclusion_item = []
    for task_id in result:
        task_result = result[task_id]
        item = None
        if task_result:
            item = ConcluderItem(task_id, task_result['exec_result']['succeed'], '')
            for maatask in task_result['exec_result']['maatasks']:
                item.append(ConcluderItem(maatask['type'], maatask['exec_result']['succeed'], '\n'.join(maatask['exec_result']['reason'])))
        else:
            item = ConcluderItem(task_id, False, 'Task failed to run')
        conclusion_item.append(item)
    conclusion_item = '\n'.join([str(i) for i in conclusion_item])

    return \
        f"""ArkHelperCLI has finished all of the tasks
{var.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{conclusion_item}"""


def web_hook(report):
    def replace_var(text: str, exec_quote=False) -> str:
        def replace_escape(es: str) -> str:
            es = es.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
            if exec_quote:
                es = quote(es)
            return es

        replace_list = [
            ('#{report}', report)
        ]  # add replacer in it to support more builtin vars
        for origin, after in replace_list:
            text = text.replace(origin, replace_escape(after))
        return text

    for webhook_config in var.global_config.get('webhook', []):
        webhook_method = webhook_config['method']
        webhook_request_body = replace_var(webhook_config['request_body']).encode()
        webhook_url = replace_var(webhook_config['url'], exec_quote=True)
        webhook_headers = webhook_config['headers']

        try:
            logging.debug(f'Start to webhook to {webhook_url}')
            webhook_response = requests.request(webhook_method, webhook_url, data=webhook_request_body, headers=webhook_headers)
            webhook_result = f'Webhook to {webhook_url}: {webhook_response.status_code}\n{webhook_response.text}'
            if webhook_response.ok:
                logging.debug(webhook_result)
            else:
                logging.warning(webhook_result)
        except Exception as e:
            logging.error(f'Webhook to {webhook_url}: {e}')


def run():
    update_nav()
    if var.global_config.get('restart_adb', False):
        ADB().exec_adb_cmd(['kill-server', 'start-server'])
    # kill_all_emulators()

    @dataclass
    class DeviceStatus:
        device: Device
        process: multiprocessing.Process | None
        process_static_params: dict | None
        process_shared_status: dict | None

    [var.tasks.append(get_full_task(personal_config)) for personal_config in var.personal_configs]
    devices = [Device(dev_config) for dev_config in var.global_config['devices']]
    statuses: list[DeviceStatus] = [DeviceStatus(_device, None, None, None) for _device in devices]
    running_result = {task.get('hash'): None for task in var.tasks}

    ...

    while True:
        ended_dev = []
        for status in statuses:
            logger = status.device.logger

            if status.process != None:
                if not status.process.is_alive():
                    task_hash = status.process_static_params["task"]["hash"]
                    logger.debug(f'TaskProcess {task_hash} ended, ready to clear')
                    running_result[task_hash] = status.process_shared_status.get('result', None)
                    status.process = None
                    status.process_static_params = None
                    status.process_shared_status = None

            if status.process == None:
                logger.debug(f'Process is None, ready to distribute task')

                def no_task():
                    logger.debug(f'No task to distribute. Ended')
                    status.device.kill()
                    ended_dev.append(status.device)
                if var.tasks:
                    distribute_task = (
                        [task for task in var.tasks if task.get('device') == status.device.alias] or
                        [task for task in var.tasks if task.get('device') is None] or
                        [None]
                    )[0]

                    if distribute_task:
                        var.tasks.remove(distribute_task)
                        process_static_params = {
                            'task': distribute_task,
                            'device': status.device
                        }
                        process_shared_status = multiprocessing.Manager().dict()
                        process = multiprocessing.Process(target=start_task_process, args=(process_static_params, process_shared_status, ))

                        status.process = process
                        status.process_static_params = process_static_params
                        status.process_shared_status = process_shared_status

                        logger.debug(f'Ready to start a task process(task={distribute_task["hash"]})')
                        process.start()
                    else:
                        no_task()
                else:
                    no_task()

        if len(ended_dev) == len(devices):
            logging.debug(f'All devices ended. Ready to exit')
            break
        else:
            time.sleep(2)

    web_hook(get_report(running_result))


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
                    current_time = datetime.now().strftime('%H:%M')
                    start_time_obj = datetime.strptime(time_start, '%H:%M')
                    end_time_obj = datetime.strptime(time_end, '%H:%M')
                    current_time_obj = datetime.strptime(current_time, '%H:%M')
                    return start_time_obj <= current_time_obj <= end_time_obj

                def date_between(date_start, date_end):
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    start_date_obj = datetime.strptime(date_start, '%Y-%m-%d')
                    end_date_obj = datetime.strptime(date_end, '%Y-%m-%d')
                    current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')
                    return start_date_obj <= current_date_obj <= end_date_obj

                def datetime_between(datetime_start, datetime_end):
                    current_datetime = datetime.now()
                    start_datetime_obj = datetime.strptime(datetime_start, '%Y-%m-%d %H:%M:%S')
                    end_datetime_obj = datetime.strptime(datetime_end, '%Y-%m-%d %H:%M:%S')
                    return start_datetime_obj <= current_datetime <= end_datetime_obj

                AM = in_game_time(datetime.now(), server).hour < 12  # in gametime
                weekday = datetime.now().weekday()
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

    hash = f'{config.get("device", "")}{server}{account_name}'
    if (index := len([t for t in var.tasks if t['hash'] == hash])) != 0:
        hash += f'_{index}'

    task = {
        'hash': hash,
        'task': final_maatasks,
        'device': config.get('device', None),
        'server': server,
        'account_name': account_name
    }
    logging.debug(f'Initialization ended for task {hash}')
    return task
