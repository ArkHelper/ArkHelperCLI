from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_tostr, load_res, update_nav
from Libs.utils import kill_processes_by_name, random_choice_with_weights, read_config, read_json, read_yaml, arknights_checkpoint_opening_time, get_game_week, arknights_package_name, write_json
import var


import logging
import os
import time
import copy
import multiprocessing
from multiprocessing import Process
import subprocess


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        # d = json.loads(details.decode('utf-8'))
        d = details.decode('utf-8')
        logging.debug(f'got callback from asst inst: {m},{arg},{d}')
    except:
        pass


def add_personal_tasks(asst: Asst, config):
    logging.debug(
        f'append task with config {config}')
    for maa_task in config['task']:
        asst.append_task(maa_task['task_name'], maa_task['task_config'])


class Device:
    def __init__(self, dev_config) -> None:
        self._adb_path = os.path.abspath(dev_config['adb_path'])
        self._start_path = dev_config['start_path']
        self.emulator_addr = dev_config['emulator_address']
        self.running_task = None
        self.alias = dev_config['alias']
        self._connected = False
        self._current_server = None
        self._asst = Asst(var.asst_res_lib_env, var.asst_res_lib_env / f'userDir_{self.alias}', asst_callback)
        self._str = f'device & asst instance {self.alias}({self.emulator_addr})'

    def __str__(self) -> str:
        return self._str

    def exec_adb(self, cmd: str):
        try:
            cmd_ls = cmd.split(' ')
            adb_command = [self._adb_path, '-s', self.emulator_addr]
            adb_command.extend(cmd_ls)

            result = subprocess.run(adb_command, capture_output=True, text=True, check=True, encoding='utf-8')
            logging.debug(f'adb output: {result.stdout}')
        except subprocess.CalledProcessError as e:
            logging.debug(f'adb exec error: {e.stderr}')
        pass

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
    
    def run_task(self, task):
        logging.info(f'{self} start run task {task["hash"]}')

        task_server = [maa_task for maa_task in task['task'] if maa_task['task_name'] == 'StartUp'][0]['task_config']['client_type']
        package_name = arknights_package_name[task_server]

        if self._current_server not in [task_server, None]:
            self.exec_adb(f'shell am force-stop {arknights_package_name[self._current_server]}')
        self.exec_adb(f'shell am start -n {package_name}/com.u8.sdk.U8UnityContext')
        time.sleep(15)

        if self._current_server != task_server.replace('Bilibili', 'Official'):
            load_res(self._asst, task_server.replace('Bilibili', 'Official'))

        self._current_server = task_server

        add_personal_tasks(self._asst, task)

        self._asst.start()

        # max_wait_time = 50*60
        while self._asst.running():
            time.sleep(5)

        self.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{int(time.time())}.png')


def start_process(shared_status, static_process_detail):
    result = shared_status['result']
    try:
        tasks = shared_status['tasks']

        device_info = static_process_detail['device']
        process_pid = static_process_detail['pid']

        dev = Device(device_info)
        dev.connect()

        while True:
            logging.info(f'Process {process_pid} start to distribute task to {dev}.')

            distribute_task = (
                [task for task in tasks if task.get('device') == dev.alias] or
                [task for task in tasks if task.get('device') is None] or
                [None]
            )[0]

            if distribute_task:
                tasks.remove(distribute_task)
                dev.run_task(distribute_task)
            else:
                logging.info(f'{dev} finished all tasks and process {process_pid} will exit.')
                break
    except Exception as e:
        logging.error(f"An expected error was occured in process {process_pid} when running: {str(e)}", exc_info=True)
