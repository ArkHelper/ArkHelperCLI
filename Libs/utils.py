import json
import pathlib
import logging
import random
from tabnanny import verbose
import psutil
import argparse
import threading
import subprocess
import os
import yaml

import pytz

import var
from jsonschema import validate
from datetime import datetime
from datetime import timedelta


def parse_arg():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    subparsers = parser.add_subparsers(title='Subcommands', dest='subcommand')

    subparser_run = subparsers.add_parser('run', help='Start running MAA according to config. ')
    subparser_test = subparsers.add_parser('test', help='Mode for develop. ')
    # subparser_run.add_argument('arg1')

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        exit(0)

    mode = args.subcommand
    verbose = args.verbose

    return mode, verbose


def get_cur_time_f():
    # 获取当前时间
    current_time = datetime.now()

    # 获取当前的小时和分钟部分
    current_hour = current_time.hour
    current_minute = current_time.minute

    # 将小时和分钟拼接成字符串
    return current_hour*100+current_minute


def read_file(path):
    with open(str(path), 'r', encoding='utf8') as file:
        return file.read()


def read_yaml(path):
    return json.loads(read_file(path))

def read_yaml(path):
    return yaml.safe_load(read_file(path))


def write_file(path, content):
    with open(str(path), 'w', encoding='utf8') as file:
        file.write(content)


def write_json(path, content):
    write_file(path, json.dumps(content))

def write_yaml(path, content):
    write_file(path, yaml.safe_dump(content)) 


def read_config(config_name):
    data = read_yaml(var.cli_env / 'Config' / f'{config_name}.yaml')
    return data


def get_logging_handlers(file_level, console_level):
    file_handler = logging.FileHandler(
        str(var.cli_env / 'Log' / 'log.log'), encoding='utf-8')
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    return [file_handler, console_handler]


def kill_processes_by_name(process_name) -> bool:
    logging.debug(f'killing process {process_name}')
    try:
        result = subprocess.run(['taskkill', '/F', '/IM', f'{process_name}.exe'], check=True, capture_output=True, text=True)
        logging.debug(f'killing result:{result.stdout}')
        return True
    except subprocess.CalledProcessError as e:
        logging.debug(f'killing result:{e.stderr}')
        return False


def get_game_time(server=''):
    zone = pytz.timezone('GMT')
    if server in ('Official', 'Bilibili', 'txwy'):
        zone = pytz.timezone('Asia/Shanghai')
        # zone = pytz.timezone('Asia/Taipei')
    elif server in ('YoStarJP', 'YoStarKR'):
        zone = pytz.timezone('Asia/Tokyo')
        # zone = pytz.timezone('Asia/Seoul')
    return (datetime.utcnow()-timedelta(hours=4)).replace(tzinfo=pytz.utc).astimezone(zone)


def get_game_week(server):
    '''
    Get weekday in the game.
    Returns an Int in 1~7, which means 周一二三四五六日 in Chinese.
    '''
    return get_game_time(server).weekday() + 1


# checkpoint_opening_time, 1~7 means 周一二三四五六日 in Chinese.
arknights_checkpoint_opening_time = {
    'SK': [1, 3, 5, 6],
    'AP': [1, 4, 6, 7],
    'CA': [2, 3, 5, 7],
    'CE': [2, 4, 6, 7],
    'LS': [1, 2, 3, 4, 5, 6, 7],
    'PR-A': [1, 4, 5, 7],
    'PR-B': [1, 2, 5, 6],
    'PR-C': [3, 4, 6, 7],
    'PR-D': [2, 3, 6, 7]
}

arknights_pack_name = {
    'Official': 'com.hypergryph.arknights',
    'Bilibili': 'com.hypergryph.arknights.bilibili',
    'YoStarJP': 'com.YoStarJP.Arknights',
    'YoStarEN': 'com.YoStarEN.Arknights',
    'YoStarKR': 'com.YoStarKR.Arknights',
    'txwy': 'tw.txwy.and.arknights'
}


def random_choice_with_weights(dict):
    # 样本数据
    items = []

    # 对应的权重
    weights = []

    for i in dict:
        items.append(i)
        weights.append(dict[i])

    return random.choices(items, weights)[0]
