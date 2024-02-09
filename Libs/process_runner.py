from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.utils import *
from Libs.model import Device
import var

import logging
import os
import time
import json
from typing import Optional, Union
import pathlib

dev: Device = None
logger: logging.Logger = None
asst: Asst = None
task: dict = None
process_str = None
task_str = None
current_maatask_status: tuple[Message, dict, object] = (None, None, None)


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        d = json.loads(details.decode('utf-8'))
        # d = details.decode('utf-8')
        process_callback(m, d, arg)
    except:
        pass


def process_callback(msg: Message, details: dict, arg):
    global dev, logger, asst, task, process_str, task_str, current_maatask_status
    logger.debug(f'Got callback: {msg},{arg},{details}.')
    if msg in [Message.TaskChainExtraInfo, Message.TaskChainCompleted, Message.TaskChainError, Message.TaskChainStopped, Message.TaskChainStart]:
        current_maatask_status = (msg, details, arg)
        logger.debug(f'current_maatask_status turned to {current_maatask_status} according to callback.')


def add_maatasks(asst: Asst, task):
    for maatask in task['task']:
        add_maatask(asst, maatask)


def add_maatask(asst: Asst, maatask):
    logger.debug(f'Append task {maatask} to {asst}.')
    asst.append_task(maatask['task_name'], maatask['task_config'])


def load_res_for_asst(asst: Asst, client_type: Optional[Union[str, None]] = None):
    incr: pathlib.Path
    if client_type in ['Official', 'Bilibili', None]:
        incr = var.maa_env / 'cache'
    else:
        incr = var.maa_env / 'resource' / 'global' / str(client_type)

    logger.debug(f'Start to load asst resource and lib from incremental path {incr}.')
    asst.load_res(incr)
    logger.debug(f'Asst resource and lib loaded from incremental path {incr}.')


def connect():
    global dev, logger, asst, task, process_str, task_str, current_maatask_status
    _execed_start = False
    while True:
        logger.debug(f'Try to connect emulator...')

        if asst.connect(dev._adb, dev._addr):
            logger.info(f'Connected to emulator.')
            break
        else:
            logger.info(f'Connect failed.')

        if not _execed_start:
            dev.kill_start()
            _execed_start = True

        time.sleep(2)
    pass


def run_maatask(maatask, time_remain) -> dict:
    global dev, logger, asst, task, process_str, task_str, current_maatask_status
    type = maatask['task_name']
    config = maatask['task_config']
    logger.info(f'Start maatask {type}, time {time_remain} sec.')

    i = 0
    max_retry_time = 4
    for i in range(max_retry_time+1):
        logger.info(f'Maatask {type} {i+1}st/{max_retry_time} trying...')
        add_maatask(asst, maatask)
        asst.start()
        logger.debug("Asst start invoked.")
        asst_stop_invoked = False
        interval = 5
        while asst.running():
            time.sleep(interval)
            time_remain -= interval
            if time_remain < 0:
                if not asst_stop_invoked and type != "Fight":
                    logger.warning(f"Task time remains {time_remain}.")
                    asst.stop()
                    logger.debug(f"Asst stop invoked.")
                    asst_stop_invoked = True
        logger.debug(f"Asst running status ended.")
        logger.debug(f"current_maatask_status={current_maatask_status}.")
        if current_maatask_status[0] == Message.TaskChainError:
            continue
        elif current_maatask_status[0] == Message.TaskChainStopped:
            break
        else:
            break

    logger.debug(f"Maatask {type} ended.")
    status_message = current_maatask_status[0]
    status_ok = status_message == Message.TaskChainCompleted
    time_ok = time_remain >= 0
    succeed = status_ok and time_ok
    if succeed:
        reason = status_message.name
    else:
        reason = ""
        if status_message == Message.TaskChainError:
            reason = status_message.name
        if not time_ok:
            reason = 'Timeout'

    logger.debug(f"Status={status_message}, time_remain={time_remain}")
    logger.info(f'Finished maatask {type} (succeed: {succeed}) beacuse of {reason}, remain {time_remain} sec.')
    return {
        "exec_result": {
            "succeed": succeed,
            "reason": reason,
            "tried_times": i+1
        },
        "time_remain": time_remain
    }


def start_task_process(process_static_params, process_shared_status):
    global dev, logger, asst, task, process_str, task_str, current_maatask_status
    dev = process_static_params['device']
    task = process_static_params['task']
    task_str = task['hash']
    task_server = task['server']
    package_name = arknights_package_name[task_server]
    process_str = f"taskprocess({task_str})"
    logger = dev.logger.getChild(process_str)
    logger.info("Created.")
    logger.info("Ready to execute task.")

    try:
        userdir: pathlib.Path = var.maa_env / f'userdir' / task_str
        userdir.parent.mkdir(exist_ok=True)
        asst = Asst(var.maa_env, var.maa_env / f'userdir' / convert_the_file_name_to_a_legal_file_name_under_windows(task_str), asst_callback)
        load_res_for_asst(asst, task_server)
        connect()

        if dev.current_status['server'] != task_server:
            if dev.current_status['server']:
                dev.exec_adb(f'shell am force-stop {arknights_package_name[dev.current_status["server"]]}')
            dev.current_status['server'] = task_server

        remain_time = 2*60*60  # sec
        for maatask in task['task']:
            if remain_time > 0:
                run_result = run_maatask(maatask, remain_time)
                remain_time = run_result['time_remain']

        dev.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{task_str}_{int(time.time())}.png')

        del asst
        logger.debug('Ready to exit.')
    except Exception as e:
        logger.error(f'An unexpected error was occured when running:{e}', exc_info=True)
