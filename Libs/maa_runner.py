from multiprocessing import Process
import random
import subprocess
from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_callback, asst_tostr, load_res, update_nav
from Libs.utils import kill_processes_by_name, random_choice_with_weights, read_config, read_yaml, arknights_checkpoint_opening_time, get_game_week, arknights_pack_name
import var

import logging
import os
import time
import copy
import multiprocessing


def run_dev(dev, tasks, info):
    dev = Device(dev, tasks, info)
    # dev.exec_adb('kill-server')
    # dev.exec_adb('start-server')
    dev.connect()
    dev.run()


def kill_all_emulators():
    for process in var.global_config['devices']:
        logging.info(f'trying to kill {process}')
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)


def run_all_devs():
    update_nav()

    var.tasks = []
    for personal_config in var.personal_configs:
        var.tasks.append(extend_full_tasks(personal_config))

    kill_all_emulators()

    processes: list[Process] = []
    task_arr = multiprocessing.Manager().list()
    task_arr.extend(var.tasks)
    for index, dev in enumerate(var.global_config['devices']):
        proc = multiprocessing.Process(target=run_dev, args=(dev, task_arr, {}))
        proc.start()
        processes.append(proc)

    while True:
        if not any([p.is_alive() for p in processes]):
            break
        time.sleep(5)

    kill_all_emulators()


def extend_full_tasks(config):
    final_tasks: list = []

    overrides = config['override']
    black_task_names = config.get('blacklist', [])
    server = ''
    for default_task in var.default_personal_config:
        default_task: dict

        final_task_config = copy.deepcopy(default_task['task_config'])
        final_task_name = copy.deepcopy(default_task['task_name'])

        preference_task_config = \
            (
                [override['task_config'] for override in overrides if override['task_name'] == final_task_name] or
                [{}]
            )[0]

        if final_task_name not in black_task_names:
            def update():
                final_task_config.update(preference_task_config)

            def append():
                final_tasks.append({
                    'task_name': final_task_name,
                    'task_config': final_task_config
                })

            # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
            # FIXME:(好像修好了)
            if final_task_name == 'StartUp':
                update()
                append()

                server = final_task_config.get('client_type', 'Official')

                if final_task_config.get('account_name', '') != '' and False:
                    another_startup_task_config = copy.deepcopy(
                        final_task_config)
                    another_startup_task_config['account_name'] = ''
                    final_tasks.append({
                        'task_name': final_task_name,
                        'task_config': another_startup_task_config
                    })
            elif final_task_name == 'Fight':
                preference_checkpoint = preference_task_config.get('stage')

                if preference_checkpoint and type(preference_checkpoint) is dict:
                    checkpoints_in_limit_list = [cp for cp in preference_checkpoint if cp.rsplit('-', 1)[0] in arknights_checkpoint_opening_time]
                    checkpoints_outof_limit_list = [cp for cp in preference_checkpoint if not cp.rsplit('-', 1)[0] in arknights_checkpoint_opening_time]

                    for checkpoint in checkpoints_in_limit_list:
                        opening_time = arknights_checkpoint_opening_time[checkpoint.rsplit('-', 1)[0]]

                        if get_game_week(server) not in opening_time:
                            preference_checkpoint.pop(checkpoint)
                            continue

                        rate_standard_coefficient = len(opening_time)
                        preference_checkpoint[checkpoint] /= rate_standard_coefficient  # 平衡概率

                    for checkpoint in checkpoints_outof_limit_list:
                        preference_checkpoint[checkpoint] /= 7  # 平衡概率

                    preference_task_config['stage'] = random_choice_with_weights(preference_checkpoint)

                update()
                append()
            else:
                update()
                append()

    return {
        'task': final_tasks,
        'device': config.get('device', None)
    }


def add_personal_tasks(asst: Asst, config):
    logging.debug(
        f'append task with config {config}')
    for maa_task in config['task']:
        asst.append_task(maa_task['task_name'], maa_task['task_config'])


class Device:
    def __init__(self, dev_config, tasks, info) -> None:
        self._adb_path = os.path.abspath(dev_config['adb_path'])
        self._start_path = dev_config['start_path']

        self.emulator_addr = dev_config['emulator_address']
        self.running_task = None
        self.info = info
        self.alias = dev_config['alias']

        self._connected = False

        self._current_server = ''
        self._asst = Asst(var.asst_res_lib_env, var.asst_res_lib_env / f'userDir_{self.alias}', asst_callback)
        self._asst_str = f'device & asst instance {self.alias}({self.emulator_addr})'

        self._shared_tasks = tasks

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

            logging.debug(f'{self._asst_str} try to connect {self.emulator_addr}')

            if self._asst.connect(self._adb_path, self.emulator_addr):
                logging.info(f'{self._asst_str} connected {self.emulator_addr}')
                break

            # 启动模拟器
            if not _execedStart and self._start_path is not None:
                os.startfile(os.path.abspath(self._start_path))  # 程序结束后会自动关闭？！

                _execedStart = True

                logging.info(f'started emulator at {self._start_path}')

            time.sleep(2)
        self._connected = True

    def running(self):
        return self._asst.running()

    def run(self):
        while True:
            logging.info(f'{self._asst_str}\'s Device task manager start to distribute task.')

            distribute_task = (
                [task for task in self._shared_tasks if task.get('device') == self.alias] or
                [task for task in self._shared_tasks if task.get('device') is None] or
                [None]
            )[0]

            if distribute_task:
                self._shared_tasks.remove(distribute_task)
                self.run_task(distribute_task)
            else:
                logging.info(f'{self._asst_str} finished all tasks and self.run() exited.')
                break

    def run_task(self, task):
        logging.info(f'{self._asst_str} start run task {task}')

        server = [maa_task for maa_task in task['task'] if maa_task['task_name'] == 'StartUp'][0]['task_config']['client_type']

        self.exec_adb(f'shell am start -n {arknights_pack_name[server]}/com.u8.sdk.U8UnityContext')
        time.sleep(15)

        if self._current_server != server.replace('Bilibili', 'Official'):
            load_res(self._asst, server.replace('Bilibili', 'Official'))

        add_personal_tasks(self._asst, task)

        self._asst.start()

        # max_wait_time = 50*60
        while True:
            if not self._asst.running():
                break

            time.sleep(5)

        self.exec_adb(f'shell screencap -p /sdcard/DCIM/AkhCLI_{time.time()}.png')
