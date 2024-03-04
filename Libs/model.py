import multiprocessing
import os
import pathlib
import threading
import time
import logging
import json
from typing import Optional, Union

from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.utils import *


class Device:
    def __init__(self, dev_config) -> None:
        self._adb = var.global_config['adb_path']
        self.alias = dev_config['alias']
        self._path = dev_config['start_path']
        self._host = dev_config['emulator_address'].split(':')[0]
        self._port = dev_config['emulator_address'].split(':')[-1]
        self._process = dev_config.get('process')
        self.logger = logging.getLogger(str(self))
        self.current_status = multiprocessing.Manager().dict()
        self.current_status['server'] = None
        self.logger.debug(f'{self} inited')

    def __str__(self) -> str:
        return f'{self.alias}({self._addr})'

    @property
    def _addr(self) -> str:
        return f'{self._host}:{self._port}'

    def exec_adb(self, cmd: str):
        exec_adb_cmd(cmd, self._addr)

    def kill_start(self):
        if self._path is not None:
            self.logger.debug(f'Try to confirm emulator in the starting state')

            if type(self._process) == None:
                pass
            elif type(self._process) == list:
                for pim in self._process:
                    kill_processes_by_name(pim)
            elif type(self._process) == str:
                if self._process == 'mumu':
                    headless_pid = get_pid_by_port(self._port)
                    player_pid = get_MuMuPlayer_by_MuMuVMMHeadless(headless_pid)
                    for pim, pid in [('MuMuVMMHeadless', headless_pid), ('MuMuPlayer', player_pid)]:
                        self.logger.debug(f'{pim} is running(?) at process(?) {pid}')

                    if headless_pid and player_pid:
                        return
                    elif headless_pid and not player_pid:
                        # TODO/:Headless Mode?
                        kill_processes_by_pid(headless_pid)
                    elif not headless_pid and player_pid:
                        kill_processes_by_pid(player_pid)
                    else:
                        pass

            os.startfile(os.path.abspath(self._path))
            self.logger.info(f'Started emulator at {self._path}')

    def kill(self):
        self.logger.debug(f'Try to kill emulator')

        if type(self._process) == None:
            pass
        elif type(self._process) == list:
            for pim in self._process:
                kill_processes_by_name(pim)
        elif type(self._process) == str:
            if self._process == 'mumu':
                headless_pid = get_pid_by_port(self._port)
                player_pid = get_MuMuPlayer_by_MuMuVMMHeadless(headless_pid)
                kill_processes_by_pid(headless_pid)
                kill_processes_by_pid(player_pid)


class AsstProxy:

    def __init__(self, id, last_logger: logging.Logger, device: Device, asst_callback: Asst.CallBackType) -> None:
        self._proxy_id = id
        self._logger = last_logger.getChild(str(self))
        self.device = device
        self.current_maatask_status: tuple[Message, dict, object] = (None, None, None)

        self.userdir: pathlib.Path = var.maa_usrdir_path / convert_str_to_legal_filename_windows(self._proxy_id)
        self.asst = Asst(var.maa_env, self.userdir, asst_callback)

    def load_res(self, client_type: Optional[Union[str, None]] = None):
        incr: pathlib.Path
        if client_type in ['Official', 'Bilibili', None]:
            incr = var.maa_env / 'cache'
        else:
            incr = var.maa_env / 'resource' / 'global' / str(client_type)

        self._logger.debug(f'Start to load asst resource and lib from incremental path {incr}')
        if not run_in_thread(Asst.load_res, (self.asst, incr,), 2, 5, self._logger):
            raise Exception('Asst failed to load resource')
        self._logger.debug(f'Asst resource and lib loaded from incremental path {incr}')

    def connect(self):
        # TODO: kill_start() only when adb can't connect to emulator
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
        max_try_time = 4

        if type == 'Award':
            max_try_time = 1  # FIXME: maa bug，找不到抽卡会报错，因此忽略
        if type == 'Fight':
            stage = config['stage']
            standby_stage = config['standby_stage']
            config.pop('standby_stage')

        for i in range(max_try_time):
            self._logger.info(f'Maatask {type} {i+1}st/{max_try_time}max trying')

            if type == 'Fight':
                if i == 0:
                    maatask['task_config']['stage'] = stage
                else:
                    maatask['task_config']['stage'] = standby_stage

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
                if type == "StartUp":
                    self.device.exec_adb(f'shell am force-stop {arknights_package_name[self.device.current_status["server"]]}')
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
