import json
import pathlib
import logging
from jsonschema import validate


def read_config(current_path, name):
    with open(str(current_path / 'Config' / f'{name}.json'), 'r', encoding='utf8')as fp:
        json_data = json.load(fp)
        with open(str(current_path / 'Libs' / 'config_schema' / f'{name}.json'), 'r', encoding='utf8')as fp1:
            schema = json.load(fp1)
            validate(instance=json_data, schema=schema)
            return json_data

def get_logging_handlers(current_path):
    # 创建一个文件处理程序，用于将日志写入文件
    file_handler = logging.FileHandler(
        str(current_path / 'Log' / 'log.log'), encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 创建一个控制台处理程序，用于将日志输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    return [file_handler, console_handler]
