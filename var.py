import pathlib
import threading

from Libs.maa_runner import TaskAndDeviceManager

global_config: dict
personal_configs: list[dict]
cli_env: pathlib.Path
asst_res_lib_env: pathlib.Path
lock: dict[str, threading.Lock]
verbose: bool
task_and_device_manager: TaskAndDeviceManager