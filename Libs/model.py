import logging
import os
import multiprocessing

import var
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
        self.logger.debug(f'{self} inited.')

    def __str__(self) -> str:
        return f'{self.alias}({self._addr})'

    @property
    def _addr(self) -> str:
        return f"{self._host}:{self._port}"

    def exec_adb(self, cmd: str):
        exec_adb_cmd(cmd, self._addr)

    def kill_start(self):
        if self._path is not None:
            self.logger.debug(f'Try to confirm emulator in the starting state.')

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
                        self.logger.debug(f'{pim} is running(?) at process(?) {pid}.')

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
        self.logger.debug(f'Try to kill emulator.')

        kill_list = []

        if type(self._process) == None:
            pass
        elif type(self._process) == list:
            kill_list = self._process
        elif type(self._process) == str:
            if self._process == 'mumu':
                kill_list = ['MuMuVMMHeadless.exe','MuMuPlayer.exe']
                    
        for _process in kill_list:
            kill_processes_by_name(_process)
