import var
from Libs.utils import *


import logging
import os
import multiprocessing


class Device:
    def __init__(self, dev_config) -> None:
        self._adb = var.global_config['adb_path']
        self.alias = dev_config['alias']
        self._path = dev_config['start_path']
        self._host = dev_config['emulator_address'].split(':')[0]
        self._port = dev_config['emulator_address'].split(':')[-1]
        self._process_names = dev_config['process_name']
        self.logger = logging.getLogger(str(self))
        self.current_status = multiprocessing.Manager().dict()
        self.current_status['server'] = None

    def __str__(self) -> str:
        return f'{self.alias}({self._addr})'

    @property
    def _addr(self):
        return f"{self._host}:{self._port}"

    def exec_adb(self, cmd: str):
        exec_adb_cmd(cmd, self._addr)

    def kill_start(self):
        if self._path is not None:
            emulator_pid = get_pid_by_port(self._addr.split(":")[-1])
            kill_processes_by_pid(emulator_pid)
            try:
                kill_processes_by_pid(get_MuMuPlayer_by_MuMuVMMHeadless(emulator_pid))
            except:
                pass

            os.startfile(os.path.abspath(self._path))
            self.logger.info(f'Started emulator at {self._path}')
