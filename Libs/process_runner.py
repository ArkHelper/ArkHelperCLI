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
        self._str = f'device {self.alias}({self.emulator_addr})'
        self._current_server = None
        self._current_maatask_status: tuple[Message, dict, object] = (None, None, None)

    def __str__(self) -> str:
        return self._str

    def process_callback(self, msg: Message, details: dict, arg):
        logging.debug(f'{self} got callback: {msg},{arg},{details}')
        if msg in [Message.TaskChainExtraInfo, Message.TaskChainCompleted, Message.TaskChainError, Message.TaskChainStopped, Message.TaskChainStart]:
            self._current_maatask_status = (msg, details, arg)
            logging.debug(f'{self} _current_maatask_status turned to {self._current_maatask_status} according to callback.')

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
                logging.info(f'{self} started emulator at {self._start_path}')

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
            self._current_server = task_server

        remain_time = 2*60*60  # sec
        for maatask in task['task']:
            if remain_time > 0:
                run_result = self.run_maatask(maatask, remain_time)
                remain_time = run_result['time_remain']

        self.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{int(time.time())}.png')

    #TODO:need pref
    def run_maatask(self, maatask, time_remain) -> dict:
        type = maatask['task_name']
        config = maatask['task_config']
        logging.info(f'{self} start maatask {type}, time {time_remain} sec.')

        i = 0
        max_retry_time = 4
        for i in range(max_retry_time+1):
            logging.info(f'{self} maatask {type} {i+1}st trying...')
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

        logging.info(f'{self} finished maatask {type} (succeed: {succeed}) beacuse of {reason}, remain {time_remain} sec.')
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
        global dev
        dev = Device(device_info)
        logging.info(f"{process_str} created which binds device {dev}.")

        while True:
            logging.debug(f'{process_str} start to distribute task to {dev}.')

            distribute_task = (
                [task for task in tasks if task.get('device') == dev.alias] or
                [task for task in tasks if task.get('device') is None] or
                [None]
            )[0]

            if distribute_task:
                try:
                    logging.debug(f'Distribute task {distribute_task["hash"]} to {dev}')
                    tasks.remove(distribute_task)
                    dev.run_task(distribute_task)
                except Exception as e:
                    # result.append()
                    pass
            else:
                logging.info(f'{dev} finished all tasks.')
                logging.debug(f'{process_str} will exit.')
                break
    except Exception as e:
        logging.error(f"An expected error was occured in {process_str} when running: {str(e)}", exc_info=True)
