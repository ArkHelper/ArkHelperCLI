import var
from Libs.utils import *
from Libs.test import test
from Libs.maa_runner import run

mode, verbose = parse_arg()

var.start_time = datetime.now()
var.cli_env = Path(__file__, '../')
var.data_path = var.cli_env / 'Data'
var.config_path = var.data_path / 'Config'
var.log_path = var.data_path / 'Log'
var.static_path = var.data_path / 'Static'

mk_CLI_dir()

var.global_config = read_config('global')
var.personal_configs = read_config('personal')
var.default_personal_config = read_config('default_personal')
var.tasks = []
var.maa_env = Path(var.global_config['maa_path'])
var.verbose = verbose

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers())

if __name__ == '__main__':
    logging.info(f'CLI started up at {var.cli_env}')
    logging.debug(f'With MAA {var.maa_env}')
    logging.debug(f'With global config {var.global_config}')
    logging.debug(f'With default personal config {var.default_personal_config}')
    logging.debug(f'With personal config {var.personal_configs}')

    try:
        entrance = None
        if mode == 'test':
            entrance = test
        elif mode == 'run':
            entrance = run

        if var.verbose and False:
            profile = LineProfiler(entrance)
            profile.runcall(entrance)
            profile.print_stats()
        else:
            entrance()

        logging.info(f'CLI ready to exit')

    except Exception as e:
        logging.critical(f'An unexpected error was occured when running: {e}', exc_info=True)
