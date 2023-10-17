import json
import pathlib
from jsonschema import validate


def read_config(current_path, name):
    with open(str(current_path / 'Config' / f'{name}.json'), 'r', encoding='utf8')as fp:
        json_data = json.load(fp)
        with open(str(current_path / 'Libs' / 'config_schema' / f'{name}.json'), 'r', encoding='utf8')as fp1:
            schema = json.load(fp1)
            validate(instance=json_data, schema=schema)
            return json_data
