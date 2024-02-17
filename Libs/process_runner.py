import pathlib
import threading
import time
import logging
import json
from typing import Optional, Union

from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.model import Device, AsstProxy
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

    try:
        asstproxy = AsstProxy(task_id, logger, device, asst_callback)
        asstproxy.load_res(task_server)
        asstproxy.connect()

        if device.current_status['server'] != task_server:
            if device.current_status['server']:
                device.exec_adb(f'shell am force-stop {arknights_package_name[device.current_status["server"]]}')
            device.current_status['server'] = task_server

        remain_time = 2*60*60  # sec
        for maatask in task['task']:
            if remain_time > 0:
                run_result = asstproxy.run_maatask(maatask, remain_time)
                remain_time = run_result['time_remain']

        # dev.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{id}_{int(time.time())}.png')

        del asstproxy
        logger.debug('Ready to exit')
    except Exception as e:
        logger.error(f'An unexpected error was occured when running:{e}', exc_info=True)
