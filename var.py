import pathlib
import threading

tasks: list[dict]
global_config: dict
personal_configs: list[dict]
default_personal_config: dict
cli_env: pathlib.Path
asst_res_lib_env: pathlib.Path
verbose: bool
start_time:int