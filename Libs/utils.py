import json
import pathlib
import logging
import psutil
import threading
import subprocess
import os

import var
from jsonschema import validate
from datetime import datetime


def get_cur_time_f():
    # 获取当前时间
    current_time = datetime.now()

    # 获取当前的小时和分钟部分
    current_hour = current_time.hour
    current_minute = current_time.minute

    # 将小时和分钟拼接成字符串
    return current_hour*100+current_minute


def read_json(path):
    with open(str(path), 'r', encoding='utf8') as json_file:
        data = json.load(json_file)
        return data


def read_config_and_validate(config_name):
    json_data = read_json(var.cli_env / 'Config' / f'{config_name}.json')
    json_schema = read_json(var.cli_env / 'Libs' /
                            'json' / 'config_schema' / f'{config_name}.json')
    validate(instance=json_data, schema=json_schema)
    return json_data


def get_logging_handlers(file_level, console_level):
    file_handler = logging.FileHandler(
        str(var.cli_env / 'Log' / 'log.log'), encoding='utf-8')
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    return [file_handler, console_handler]


def kill_processes_by_name(process_name) -> bool:
    logging.debug(f"killing process {process_name}")
    try:
        result = subprocess.run(['taskkill', '/F', '/IM', f'{process_name}.exe'], check=True, capture_output=True, text=True)
        logging.debug(f"killing result:{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.debug(f"killing result:{e.stderr}")
        return False
