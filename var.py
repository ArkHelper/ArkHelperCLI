import pathlib
import threading

global_config: dict
personal_configs: list[dict]
cli_env: pathlib.Path
asst_res_lib_env: pathlib.Path
lock: dict[str, threading.Lock]