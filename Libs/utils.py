import json
import pathlib
import logging
import random
import psutil
import threading
import subprocess
import os

import pytz

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

def get_server_time(server):
    zone = pytz.timezone('GMT')
    if server in ('Official','Bilibili','txwy'):
        zone = pytz.timezone('Asia/Shanghai')
        #zone = pytz.timezone('Asia/Taipei')
    elif server in ('YoStarJP','YoStarKR'):
        zone = pytz.timezone('Asia/Tokyo')
        #zone = pytz.timezone('Asia/Seoul')
    

    return datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(zone)
    pass

arknights_checkpoint_opening_time = {
    "SK": [1,3,5,6],
    "AP": [1,4,6,7],
    "CA": [2,3,5,7],
    "CE": [2,4,6,7],
    "LS": [1,2,3,4,5,6,7],
    "PR-A": [1,4,5,7],
    "PR-B": [1,2,5,6],
    "PR-C": [3,4,6,7],
    "PR-D": [2,3,6,7]
}

arknights_pack_name = {
    'Official':'com.hypergryph.arknights',
    'Bilibili':'com.hypergryph.arknights.bilibili',
    'txwy':'com.YoStarJP.Arknights',
    'YoStarEN':'com.YoStarEN.Arknights',
    'YoStarJP':'com.YoStarKR.Arknights',
    'YoStarKR':'tw.txwy.and.arknights'
}

def random_choice_with_weights(dict):
    # 样本数据
    items = []

    # 对应的权重
    weights = []

    for i in dict :
        items.append(i)
        weights.append(dict[i])

    return random.choices(items, weights)[0]