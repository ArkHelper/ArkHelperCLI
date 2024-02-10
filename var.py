from datetime import datetime
from pathlib import Path

tasks: list[dict]
global_config: dict
personal_configs: list[dict]
default_personal_config: dict
cli_env: Path
data_path: Path
config_path : Path
log_path: Path
static_path: Path
maa_env: Path
verbose: bool
start_time:datetime