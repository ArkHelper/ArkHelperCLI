import json
import pathlib
import logging
import psutil
import threading
import os

import var
from jsonschema import validate
from concurrent.futures import thread


def read_config_and_validate(config_name):
    with open(str(var.cli_env / 'Config' / f'{config_name}.json'), 'r', encoding='utf8')as fp:
        json_data = json.load(fp)
        with open(str(var.cli_env / 'Libs' / 'config_schema' / f'{config_name}.json'), 'r', encoding='utf8')as fp1:
            schema = json.load(fp1)
            validate(instance=json_data, schema=schema)
            return json_data


def get_logging_handlers(file_level,console_level):
    file_handler = logging.FileHandler(
        str(var.cli_env / 'Log' / 'log.log'), encoding='utf-8')
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    return [file_handler, console_handler]


def kill_processes_by_name(process_name):
    os.system(f'taskkill /F /IM {process_name}')