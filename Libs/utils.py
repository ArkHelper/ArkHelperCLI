import hashlib
import json
import logging
import random
import psutil
import argparse
import subprocess
import yaml
import pytz
from pathlib import Path
from datetime import datetime, timezone, timedelta

import var


def mk_CLI_dir():
    var.data_path.mkdir(exist_ok=True)
    var.config_path.mkdir(exist_ok=True)
    var.log_path.mkdir(exist_ok=True)
    var.static_path.mkdir(exist_ok=True)


def convert_the_file_name_to_a_legal_file_name_under_windows(filename):
    end = ""
    for char in filename:
        if not char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            end += char
    return end


def is_process_running(process_name):
    for process in psutil.process_iter(['name']):
        try:
            process_info = process.info
            if process_info['name'] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_pid_by_port(port) -> int | None:
    '''
    Can safely pass in None (return None)
    '''
    if port:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                return conn.pid
    return None


def get_process_info(pid):
    try:
        process = psutil.Process(pid)
        return process
    except psutil.NoSuchProcess as e:
        logging.error(f"Get process failed: {e}")


def exec_adb_cmd(cmd, device=None):
    try:
        adb_path = var.global_config['adb_path']
        cmd_ls = cmd.split(' ')
        adb_command = [adb_path]
        if device:
            adb_command.extend(['-s', device])
        adb_command.extend(cmd_ls)

        logging.debug(f'Execing adb cmd: {" ".join(adb_command)}.')
        result = subprocess.run(adb_command, capture_output=True, text=True, check=True, encoding='utf-8')
        logging.debug(f'adb output: {result.stdout}')
    except subprocess.CalledProcessError as e:
        logging.error(f'adb exec error: {e.stderr}')
    pass


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


def get_cur_time_f_hhmm():
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute
    return current_hour*100+current_minute


def read_file(path):
    with open(str(path), 'r', encoding='utf8') as file:
        return file.read()


def read_json(path):
    return json.loads(read_file(path))


def read_yaml(path):
    return yaml.safe_load(read_file(path))


def write_file(path, content):
    with open(str(path), 'w', encoding='utf8') as file:
        file.write(content)


def write_json(path, content):
    write_file(path, json.dumps(content, ensure_ascii=False))


def write_yaml(path, content):
    write_file(path, yaml.safe_dump(content))


def read_config(config_name):
    data = read_yaml(var.config_path / f'{config_name}.yaml')
    return data


def get_logging_handlers():
    file_level, console_level = logging.DEBUG, logging.DEBUG if var.verbose else logging.INFO
    log_file = var.log_path / 'log.log'

    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
        log_file.touch()

    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    return [file_handler, console_handler]


def kill_processes_by_name(process_name) -> bool:
    logging.info(f'killing process {process_name}')
    try:
        result = subprocess.run(['taskkill', '/F', '/IM', f'{process_name}'], check=True, capture_output=True, text=True)
        logging.debug(f'killing result:{result.stdout}')
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f'killing result:{e.stderr}')
        return False


def kill_processes_by_pid(pid) -> bool:
    logging.info(f'killing process {pid}')
    try:
        result = subprocess.run(['taskkill', '/F', '/PID', f'{pid}'], check=True, capture_output=True, text=True)
        logging.debug(f'Killing result:{result.stdout}.')
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f'Killing result:{e.stderr}.')
        return False


def get_process_command_line(pid):
    try:
        process = psutil.Process(pid)
        command_line = process.cmdline()
        return command_line
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error: {e}")
        return None


def get_process_start_location(pid):
    try:
        process = psutil.Process(pid)
        start_location = process.exe()
        return start_location
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error: {e}")
        return None


def get_pids_by_process_name(process_name):
    matching_pids = []
    for process in psutil.process_iter(['pid', 'name']):
        try:
            process_info = process.info
            if process_info['name'] == process_name:
                matching_pids.append(process_info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return matching_pids


def prase_MuMuVMMHeadless_commandline(headless_pid) -> dict:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--comment')

    parsed, unknown = parser.parse_known_args(get_process_command_line(headless_pid)[1:])
    return {
        "index": parsed.comment.split('-')[-1]
    }


def prase_MuMuPlayer_commandline(player_pid) -> dict:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-v')

    parsed, unknown = parser.parse_known_args(get_process_command_line(player_pid)[1:])
    return {
        "index": parsed.v if parsed.v else '0'
    }


def get_MuMuPlayer_by_MuMuVMMHeadless(headless_pid) -> int | None:
    '''
    Can safely pass in None (return None)
    '''
    if not headless_pid:
        return None
    index = prase_MuMuVMMHeadless_commandline(headless_pid)['index']
    player_pids = [p for p in get_pids_by_process_name('MuMuPlayer.exe') if prase_MuMuPlayer_commandline(p)['index'] == index]
    if player_pids:
        return player_pids[0]
    else:
        return None


def in_game_time(time, server='Official'):
    zone = pytz.timezone('GMT')
    if server in ('Official', 'Bilibili', 'txwy'):
        zone = pytz.timezone('Asia/Shanghai')
        # zone = pytz.timezone('Asia/Taipei')
    elif server in ('YoStarJP', 'YoStarKR'):
        zone = pytz.timezone('Asia/Tokyo')
        # zone = pytz.timezone('Asia/Seoul')
    elif server == '':
        zone = pytz.timezone('Asia/Shanghai')
    return (time.astimezone(timezone.utc)-timedelta(hours=4)).replace(tzinfo=pytz.utc).astimezone(zone)


def in_game_week(time, server):
    '''
    Get weekday in the game.
    Returns an Int in 1~7, which means 周一二三四五六日 in Chinese.
    '''
    return in_game_time(time, server).weekday() + 1


def byte_to_MB(byte):
    return byte / (1024**2)


def adjust_log_file():
    log_file = var.log_path / 'log.log'
    log_backup_file = var.log_path / 'log.log.bak'
    if log_file.exists():
        if byte_to_MB(log_file.stat().st_size) > 20:
            if log_backup_file.exists():
                log_backup_file.unlink()
            log_file.rename(log_backup_file)


# stage_opening_time, 1~7 means 周一二三四五六日 in Chinese.
arknights_stage_opening_time = {
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

arknights_package_name = {
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


def generate_hash(input_string):
    # 使用SHA-256哈希函数
    hash_object = hashlib.sha256(input_string.encode())
    # 获取十六进制表示的哈希值
    hex_dig = hash_object.hexdigest()
    # 截取前六位作为哈希
    six_digit_hash = hex_dig[:6]
    return six_digit_hash
