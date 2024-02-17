import pathlib
import threading
import time
import logging
import json
from typing import Optional, Union

from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.model import Device
from Libs.utils import *


logger: logging.Logger = None
asstproxy: 'AsstProxy' = None
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


class AsstProxy:

    def __init__(self, id, last_logger: logging.Logger, device: Device) -> None:
        self._proxy_id = id
        self._logger = last_logger.getChild(str(self))
        self.device = device
        self.current_maatask_status: tuple[Message, dict, object] = (None, None, None)

        self.userdir: pathlib.Path = var.maa_env / f'userdir' / convert_the_file_name_to_a_legal_file_name_under_windows(self._proxy_id)
        self.asst = Asst(var.maa_env, self.userdir, asst_callback)

    def load_res(self, client_type: Optional[Union[str, None]] = None):
        incr: pathlib.Path
        if client_type in ['Official', 'Bilibili', None]:
            incr = var.maa_env / 'cache'
        else:
            incr = var.maa_env / 'resource' / 'global' / str(client_type)

        self._logger.debug(f'Start to load asst resource and lib from incremental path {incr}')
        max_retry_time = 5
        for try_time in range(max_retry_time):
            self._logger.debug(f'Load asst resource {try_time+1}st/{max_retry_time+1} trying')
            thread = threading.Thread(target=Asst.load_res, args=(self.asst, incr,))
            thread.start()
            thread.join(10)
            if thread.is_alive():
                self._logger.debug(f'Load asst resource {try_time+1}st/{max_retry_time+1} failed')
            else:
                break
        self._logger.debug(f'Asst resource and lib loaded from incremental path {incr}')

    def connect(self):
        # FIXME: kill_start() only when adb can't connect to emulator
        # _execed_start = False

        self.device.kill_start()
        while True:
            self._logger.debug(f'Try to connect emulator')

            if self.asst.connect(self.device._adb, self.device._addr):
                self._logger.debug(f'Connected to emulator')
                break
            else:
                self._logger.debug(f'Connect failed')

            # if not _execed_start:
            #    self.device.kill_start()
            #    _execed_start = True

            time.sleep(2)

    def add_maatask(self, maatask):
        self._logger.debug(f'Ready to append task {maatask} to {self}')
        self.asst.append_task(maatask['task_name'], maatask['task_config'])

    def add_maatasks(self, task):
        for maatask in task['task']:
            self.add_maatask(maatask)

    def process_callback(self, msg: Message, details: dict, arg):
        self._logger.debug(f'Got callback: {msg},{arg},{details}')
        if msg in [Message.TaskChainExtraInfo, Message.TaskChainCompleted, Message.TaskChainError, Message.TaskChainStopped, Message.TaskChainStart]:
            self.current_maatask_status = (msg, details, arg)
            self._logger.debug(f'current_maatask_status turned to {self.current_maatask_status} according to callback')

    def run_maatask(self, maatask, time_remain) -> dict:
        type = maatask['task_name']
        config = maatask['task_config']
        self._logger.info(f'Start maatask {type}, time {time_remain} sec')

        i = 0
        max_retry_time = 4
        if type == 'Award':
            max_retry_time = 1  # FIXME: maa bug，找不到抽卡会报错，因此忽略
        for i in range(max_retry_time+1):
            self._logger.info(f'Maatask {type} {i+1}st/{max_retry_time+1}max trying')
            self.add_maatask(maatask)
            self.asst.start()
            self._logger.debug('Asst start invoked')
            asst_stop_invoked = False
            interval = 5
            while self.asst.running():
                time.sleep(interval)
                time_remain -= interval
                if time_remain < 0:
                    if not asst_stop_invoked and type != 'Fight':
                        self._logger.warning(f'Task time remains {time_remain}')
                        self.asst.stop()
                        self._logger.debug(f'Asst stop invoked')
                        asst_stop_invoked = True
            self._logger.debug(f'Asst running status ended')
            self._logger.debug(f'current_maatask_status={self.current_maatask_status}')
            if self.current_maatask_status[0] == Message.TaskChainError:
                continue
            elif self.current_maatask_status[0] == Message.TaskChainStopped:
                break
            else:
                break

        self._logger.debug(f'Maatask {type} ended')
        status_message = self.current_maatask_status[0]
        status_ok = status_message == Message.TaskChainCompleted
        time_ok = time_remain >= 0
        succeed = status_ok and time_ok
        if succeed:
            reason = status_message.name
        else:
            reason = ''
            if status_message == Message.TaskChainError:
                reason = status_message.name
            if not time_ok:
                reason = 'Timeout'

        self._logger.debug(f'Status={status_message}, time_remain={time_remain}')
        if succeed:
            self._logger.info(f'Maatask {type} ended successfully beacuse of {reason}')
        else:
            self._logger.warning(f'Maatask {type} ended in failure beacuse of {reason}')
        return {
            'exec_result': {
                'succeed': succeed,
                'reason': reason,
                'tried_times': i+1
            },
            'time_remain': time_remain
        }

    def __str__(self) -> str:
        return f'asstproxy({self._proxy_id})'

    def __del__(self):
        del self.asst


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
        asstproxy = AsstProxy(task_id, logger, device)
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
