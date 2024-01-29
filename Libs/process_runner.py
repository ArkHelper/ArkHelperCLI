import queue
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_tostr, load_res_for_asst, update_nav
from Libs.utils import exec_adb_cmd, kill_processes_by_name, random_choice_with_weights, read_config, read_json, read_yaml, arknights_checkpoint_opening_time, get_game_week, arknights_package_name, write_json
import var


import logging
import os
import time
import json
import copy
import multiprocessing
from multiprocessing import Process
import subprocess

dev: 'Device' = None


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        d = json.loads(details.decode('utf-8'))
        # d = details.decode('utf-8')
        dev.process_callback(m, d, arg)
    except:
        pass


def add_maatasks(asst: Asst, task):
    for maatask in task['task']:
        add_maatask(maatask)


def add_maatask(asst: Asst, maatask):
    logging.debug(f'append task {maatask} to {asst}')
    asst.append_task(maatask['task_name'], maatask['task_config'])


class Device:
    def __init__(self, dev_config) -> None:
        self._adb_path = var.global_config['adb_path']
        self._start_path = dev_config['start_path']
        self.emulator_addr = dev_config['emulator_address']
        # self.running_task = None
        self.alias = dev_config['alias']
        self._asst = None
        self._connected = False
        self._str = f'device & asst instance {self.alias}({self.emulator_addr})'
        self._current_server = None
        self._current_maatask_status: tuple[Message, dict, object] = (None, None, None)

    def __str__(self) -> str:
        return self._str

    def process_callback(self, msg: Message, details: dict, arg):
        if msg in [Message.TaskChainExtraInfo, Message.TaskChainCompleted, Message.TaskChainError, Message.TaskChainStopped, Message.TaskChainStart]:
            self._current_maatask_status = (msg, details, arg)
        logging.debug(f'{self} got callback: {msg},{arg},{details}')

    def exec_adb(self, cmd: str):
        exec_adb_cmd(cmd, self.emulator_addr)

    def connect(self):
        _execedStart = False
        while True:
            logging.debug(f'{self} try to connect emulator')

            if self._asst.connect(self._adb_path, self.emulator_addr):
                logging.info(f'{self} connected to emulator')
                break

            if not _execedStart and self._start_path is not None:
                os.startfile(os.path.abspath(self._start_path))  # 程序结束后会自动关闭？！
                _execedStart = True
                logging.debug(f'{self} started emulator at {self._start_path}')

            time.sleep(2)
        self._connected = True

    def running(self):
        return self._asst.running()

    def run_task(self, task) -> dict:
        logging.info(f'{self} start run task {task["hash"]}')

        task_server = task['server']
        package_name = arknights_package_name[task_server]
        if self._current_server != task_server.replace('Bilibili', 'Official'):
            self._asst = Asst(var.asst_res_lib_env, var.asst_res_lib_env / f'userDir_{self.alias}', asst_callback)
            load_res_for_asst(self._asst, task_server)
            self.connect()

        if self._current_server != task_server:
            if self._current_server:
                self.exec_adb(f'shell am force-stop {arknights_package_name[self._current_server]}')
            self.exec_adb(f'shell am start -n {package_name}/com.u8.sdk.U8UnityContext')
            time.sleep(15)
            self._current_server = task_server

        remain_time = 30*60  # sec
        for maatask in task['task']:
            run_result = self.run_maatask(maatask, remain_time)
            remain_time -= run_result['time_cost']

        self.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{int(time.time())}.png')

    #TODO:need pref
    def run_maatask(self, maatask, max_time) -> dict:
        logging.info(f'{self} start run maatask {maatask}')
        type = maatask['task_name']
        config = maatask['task_config']
        this_time_cost = 0

        i = 0
        max_retry_time = 4
        for i in range(max_retry_time+1):
            add_maatask(self._asst, maatask)
            self._asst.start()
            while self._asst.running():
                interval = 5
                time.sleep(interval)
                this_time_cost += interval
                if max_time <= this_time_cost:
                    self._asst.stop()
                    break
            if self._current_maatask_status[0] == Message.TaskChainError:
                continue
            else:
                break

        succeed = self._current_maatask_status[0] == Message.TaskChainCompleted and max_time > this_time_cost

        return {
            "exec_result": {
                "succeed": succeed,
                "reason": self._current_maatask_status[0].name if max_time > this_time_cost else 'timeout',
                "tried_times": i+1
            },
            "time_cost": this_time_cost
        }


def start_process(shared_status, static_process_detail):
    result = shared_status['result']
    try:
        tasks = shared_status['tasks']

        device_info = static_process_detail['device']
        process_pid = static_process_detail['pid']

        global dev
        dev = Device(device_info)

        while True:
            logging.info(f'Process {process_pid} start to distribute task to {dev}.')

            distribute_task = (
                [task for task in tasks if task.get('device') == dev.alias] or
                [task for task in tasks if task.get('device') is None] or
                [None]
            )[0]

            if distribute_task:
                try:
                    tasks.remove(distribute_task)
                    dev.run_task(distribute_task)
                except Exception as e:
                    # result.append()
                    pass
            else:
                logging.info(f'{dev} finished all tasks and process {process_pid} will exit.')
                break
    except Exception as e:
        logging.error(f"An expected error was occured in process {process_pid} when running: {str(e)}", exc_info=True)
