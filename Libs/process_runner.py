from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.utils import *
import var

import logging
import os
import time
import json
from typing import Optional, Union
import pathlib

_dev: 'Device' = None
_logger: logging.Logger = None


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        d = json.loads(details.decode('utf-8'))
        # d = details.decode('utf-8')
        _dev.process_callback(m, d, arg)
    except:
        pass


def add_maatasks(asst: Asst, task):
    for maatask in task['task']:
        add_maatask(asst, maatask)


def add_maatask(asst: Asst, maatask):
    _logger.debug(f'Append task {maatask} to {asst}')
    asst.append_task(maatask['task_name'], maatask['task_config'])


def load_res_for_asst(asst: Asst, client_type: Optional[Union[str, None]] = None):
    incr: pathlib.Path
    if client_type in ['Official', 'Bilibili', None]:
        incr = var.maa_env / 'cache'
    else:
        incr = var.maa_env / 'resource' / 'global' / str(client_type)

    _logger.debug(f'Start to load asst resource and lib from incremental path {incr}')
    asst.load_res(incr)
    _logger.debug(f'Asst resource and lib loaded from incremental path {incr}')


class Device:
    def __init__(self, dev_config) -> None:
        self._adb_path = var.global_config['adb_path']
        self._start_path = dev_config['start_path']
        _addr = dev_config['emulator_address'].split(':')
        self._host = _addr[0]
        self._port = _addr[-1]
        self.alias = dev_config['alias']
        self._process_names = dev_config['process_name']
        # self.running_task = None
        self._asst = None
        self._connected = False
        self._current_server = None
        self._current_maatask_status: tuple[Message, dict, object] = (None, None, None)
        self._logger = _logger.getChild(str(self))

    def __str__(self) -> str:
        return f'{self.alias}({self._addr})'
    
    @property
    def _addr(self):
        return f"{self._host}:{self._port}"

    def process_callback(self, msg: Message, details: dict, arg):
        self._logger.debug(f'Got callback: {msg},{arg},{details}')
        if msg in [Message.TaskChainExtraInfo, Message.TaskChainCompleted, Message.TaskChainError, Message.TaskChainStopped, Message.TaskChainStart]:
            self._current_maatask_status = (msg, details, arg)
            self._logger.debug(f'_current_maatask_status turned to {self._current_maatask_status} according to callback.')

    def exec_adb(self, cmd: str):
        exec_adb_cmd(cmd, self._addr)

    def connect(self):
        _execedStart = False
        while True:
            self._logger.debug(f'Try to connect emulator')

            if self._asst.connect(self._adb_path, self._addr):
                self._logger.info(f'Connected to emulator')
                break
            else:
                self._logger.info(f'Connect failed')

            if not _execedStart and self._start_path is not None:
                emulator_pid = get_pid_by_port(self._addr.split(":")[-1])
                kill_processes_by_pid(emulator_pid)
                try:
                    kill_processes_by_pid(get_MuMuPlayer_by_MuMuVMMHeadless(emulator_pid))
                except:
                    pass

                os.startfile(os.path.abspath(self._start_path))
                self._logger.info(f'Started emulator at {self._start_path}')
                _execedStart = True

            time.sleep(2)
        self._connected = True

    def running(self):
        return self._asst.running()

    def run_task(self, task) -> dict:
        self._logger.info(f'Start run task {task["hash"]}')

        task_server = task['server']
        package_name = arknights_package_name[task_server]
        if self._current_server != task_server.replace('Bilibili', 'Official'):
            del self._asst
            self._asst = Asst(var.maa_env, var.maa_env / f'userDir_{self.alias}', asst_callback)
            load_res_for_asst(self._asst, task_server)
            self.connect()

        if self._current_server != task_server:
            if self._current_server:
                self.exec_adb(f'shell am force-stop {arknights_package_name[self._current_server]}')
            self._current_server = task_server

        remain_time = 2*60*60  # sec
        for maatask in task['task']:
            if remain_time > 0:
                run_result = self.run_maatask(maatask, remain_time)
                remain_time = run_result['time_remain']

        self.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{int(time.time())}.png')

    def run_maatask(self, maatask, time_remain) -> dict:
        type = maatask['task_name']
        config = maatask['task_config']
        self._logger.info(f'Start maatask {type}, time {time_remain} sec.')

        i = 0
        max_retry_time = 4
        for i in range(max_retry_time+1):
            self._logger.info(f'Maatask {type} {i+1}st trying...')
            add_maatask(self._asst, maatask)
            self._asst.start()
            asst_stop_invoked = False
            interval = 5
            while self._asst.running():
                time.sleep(interval)
                time_remain -= interval
                if time_remain < 0:
                    if not asst_stop_invoked and type != "Fight":
                        self._asst.stop()
                        asst_stop_invoked = True
            if self._current_maatask_status[0] == Message.TaskChainError:
                continue
            elif self._current_maatask_status[0] == Message.TaskChainStopped:
                break
            else:
                break

        status_message = self._current_maatask_status[0]
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

        self._logger.info(f'Finished maatask {type} (succeed: {succeed}) beacuse of {reason}, remain {time_remain} sec.')
        return {
            "exec_result": {
                "succeed": succeed,
                "reason": reason,
                "tried_times": i+1
            },
            "time_remain": time_remain
        }


def start_process(shared_status, static_process_detail):
    try:
        result = shared_status['result']
        tasks = shared_status['tasks']
        device_info = static_process_detail['device']
        process_pid = static_process_detail['pid']
        process_str = f"process{process_pid}"
        global _logger
        _logger = logging.getLogger(process_str)
        global _dev
        _dev = Device(device_info)
        _logger.info(f"Created which binds device {_dev}.")

        while True:
            _logger.debug(f'{process_str} start to distribute task to {_dev}.')

            distribute_task = (
                [task for task in tasks if task.get('device') == _dev.alias] or
                [task for task in tasks if task.get('device') is None] or
                [None]
            )[0]

            if distribute_task:
                try:
                    _logger.debug(f'Distribute task {distribute_task["hash"]} to {_dev}')
                    tasks.remove(distribute_task)
                    _dev.run_task(distribute_task)
                except Exception as e:
                    # result.append()
                    pass
            else:
                _logger.info(f'{_dev} finished all tasks.')
                _logger.debug(f'{process_str} will exit.')
                break
    except Exception as e:
        _logger.error(f"An unexpected error was occured in {process_str} when running: {str(e)}", exc_info=True)
