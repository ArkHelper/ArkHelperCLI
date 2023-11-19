from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_callback, asst_tostr, load_res, update_nav
from Libs.utils import kill_processes_by_name, random_choice_with_weights, read_config_and_validate, read_json, arknights_checkpoint_opening_time, get_server_time
import var

import logging
import os
import time
import copy


async def run_all_devs():
    update_nav()

    var.task_and_device_manager._tasks = {}
    var.personal_configs = read_config_and_validate("personal")
    personal_default = read_json(
        var.cli_env / "Libs" / "json" / "default" / "personal.json")
    for personal_config in var.personal_configs:
        var.task_and_device_manager.add_task(
            extend_full_tasks(personal_config, personal_default))
        pass

    load_res(None)

    for process in var.global_config['devices']:
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)

    time.sleep(5)

    for dev in var.global_config["devices"]:
        var.task_and_device_manager.add_device(Device(dev))

    var.task_and_device_manager.start()

    for process in var.global_config['devices']:
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)


def extend_full_tasks(config, defaults):
    final_tasks: list = []

    config_tasks = config["task"]
    black_task_names = config.get("blacklist", [])
    server = ""
    for default_task in defaults:
        default_task: dict

        final_task_config = copy.deepcopy(default_task["task_config"])
        final_task_name = copy.deepcopy(default_task["task_name"])

        preference_task_config = config_tasks.get(final_task_name, {})

        if final_task_name not in black_task_names:
            def update():
                final_task_config.update(preference_task_config)

            def append():
                final_tasks.append({
                    "task_name": final_task_name,
                    "task_config": final_task_config
                })

            # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
            # FIXME:(好像修好了)
            if final_task_name == "StartUp":
                update()
                append()

                server = final_task_config.get("client_type", "Official")

                if final_task_config.get("account_name", "") != "" and False:
                    another_startup_task_config = copy.deepcopy(
                        final_task_config)
                    another_startup_task_config["account_name"] = ""
                    final_tasks.append({
                        "task_name": final_task_name,
                        "task_config": another_startup_task_config
                    })
            elif final_task_name == "Fight":
                preference_checkpoint = preference_task_config.get("stage")

                if preference_checkpoint and type(preference_checkpoint) is dict:
                    checkpoints_in_limit_list = [cp for cp in preference_checkpoint if cp.rsplit("-", 1)[0] in arknights_checkpoint_opening_time]
                    checkpoints_outof_limit_list = [cp for cp in preference_checkpoint if not cp.rsplit("-", 1)[0] in arknights_checkpoint_opening_time]

                    for checkpoint in checkpoints_in_limit_list:
                        opening_time = arknights_checkpoint_opening_time[checkpoint.rsplit("-", 1)[0]]

                        if get_server_time(server).weekday()+1 not in opening_time:
                            preference_checkpoint.pop(checkpoint)
                            continue

                        rate_standard_coefficient = len(opening_time)
                        preference_checkpoint[checkpoint] /= rate_standard_coefficient  # 平衡概率

                    for checkpoint in checkpoints_outof_limit_list:
                        preference_checkpoint[checkpoint] /= 7  # 平衡概率

                    preference_task_config["stage"] = random_choice_with_weights(preference_checkpoint)

                update()
                append()
            else:
                update()
                append()

    return {
        "task": final_tasks,
        "device": config.get("device", None)
    }


def add_personal_tasks(asst: Asst, config):
    logging.info(
        f'append task with config {config}')
    for maa_task in config["task"]:
        asst.append_task(maa_task["task_name"], maa_task["task_config"])


class Device:
    def __init__(self, dev_config) -> None:
        self._adb_path = os.path.abspath(dev_config["adb_path"])
        self._start_path = dev_config["start_path"]

        self.emulator_addr = dev_config["emulator_address"]
        self.running_task = None

        self._connected = False

        self._asst = Asst(asst_callback)
        self._asst_str = asst_tostr(self.emulator_addr)

        if not self._connected:
            _execStart = False
            while True:

                logging.debug(
                    f"{self._asst_str} try to connect {self.emulator_addr}")

                if self._asst.connect(self._adb_path, self.emulator_addr):
                    logging.debug(
                        f"{self._asst_str} connected {self.emulator_addr}")
                    break

                # 启动模拟器
                if not _execStart and self._start_path is not None:
                    os.startfile(os.path.abspath(
                        self._start_path))  # 程序结束后会自动关闭？！
                    _execStart = True

                    logging.debug(f"started emulator at {self._start_path}")

                time.sleep(2)

            # time.sleep(15)
            self._connected = True

    def running(self):
        return self._asst.running()

    def run_task(self, task):

        add_personal_tasks(self._asst, task)

        max_wait_time = 50*60

        self._asst.start()

        logging.info(f"{self._asst_str} done task {task}")


class TaskAndDeviceManager:
    _devices: list[Device] = []
    _tasks = {}

    def add_device(self, device):
        self._devices.append(device)
        pass

    def add_task(self, task):
        server = [maa_task for maa_task in task["task"] if maa_task["task_name"] == "StartUp"][0]["task_config"]["client_type"].replace("Bilibili", "Official")

        self._tasks.setdefault(server, []).append(task)

    def start(self):
        while len(self._tasks) != 0:
            time.sleep(5)

            current_server, current_server_task_list = None, None

            def update_cur():
                nonlocal current_server, current_server_task_list
                current_server = next(iter(self._tasks.keys()), None)
                current_server_task_list = self._tasks.get(current_server, None)

            # TODO:逻辑还需要优化，比如第一列如果不是国服呢？
            update_cur()

            if current_server_task_list:
                idle_devices = [device for device in self._devices if not device.running()]
                for device in idle_devices:
                    distribute_task = (
                        [task for task in current_server_task_list if task.get('device') == device.emulator_addr] or
                        [task for task in current_server_task_list if task.get('device') is None] or
                        [None]
                    )[0]

                    if distribute_task:
                        device.run_task(distribute_task)
                        current_server_task_list.remove(distribute_task)

            all_devices_idle: bool = all(not device.running() for device in self._devices)
            if all_devices_idle:
                self._tasks.pop(current_server)
                update_cur()
                if current_server:
                    load_res(current_server)
