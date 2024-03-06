import pathlib
import threading
import time
import logging
import json
from typing import Optional, Union

from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.model import *
from Libs.utils import *


logger: logging.Logger = None
asstproxy: AsstProxy = None
task: dict = None
task_id = None
process_str = None


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        d = json.loads(details.decode('utf-8'))
        asstproxy.process_callback(m, d, arg)
    except Exception as e:
        logger.error(f'An unexpected error was occured when receiving callback: {e}', exc_info=True)
        pass


def start_task_process(process_static_params, process_shared_status):
    global logger, task, task_id, process_str, asstproxy

    device: Device = process_static_params['device']
    task = process_static_params['task']
    task_id = task['hash']
    task_server = task['server']
    process_str = f'taskprocess({task_id})'
    logger = device.logger.getChild(process_str)
    logger.debug('Created')
    logger.info('Ready to execute task')

    result_succeed = False
    result_reason = []
    result_maatasks: list[MaataskRunResult] = []

    try:
        asstproxy = AsstProxy(task_id, logger, device, asst_callback)
        asstproxy.load_res(task_server)
        asstproxy.connect()

        if device.current_status['server'] != task_server:
            if device.current_status['server']:
                device.exec_adb(f'shell am force-stop {arknights_package_name[device.current_status["server"]]}')
            device.current_status['server'] = task_server

        remain_time = 2*60*60  # sec
        execute, execute_disabled_by = True, ''
        for maatask in task['task']:
            maatask_name = maatask['task_name']
            if remain_time > 0:
                if execute:
                    run_result = asstproxy.run_maatask(maatask, remain_time)
                    if maatask_name == 'StartUp' and not run_result.exec_result.succeed:
                        execute, execute_disabled_by = False, maatask_name
                    remain_time = run_result.time_remain
                    result_maatasks.append(run_result)
                else:
                    result_maatasks.append(MaataskRunResult(maatask_name, False, [f'Skipped: disabled by {execute_disabled_by}'], 0, 0))
            else:
                result_maatasks.append(MaataskRunResult(maatask_name, False, ['LackTime'], 0, 0))

        # dev.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{id}_{int(time.time())}.png')

        result_succeed = all([t.exec_result.succeed for t in result_maatasks])
        result_maatasks = [t.dict() for t in result_maatasks]

        process_shared_status['result'] = {
            'task': task_id,
            'exec_result': {
                'succeed': result_succeed,
                'reason': result_reason,
                'maatasks': result_maatasks
            }
        }

        del asstproxy
        logger.debug('Ready to exit')
    except Exception as e:
        logger.error(f'An unexpected error was occured when running: {e}', exc_info=True)
