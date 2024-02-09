import var
from Libs.utils import *
from Libs.test import test
from Libs.maa_runner import run

mode, verbose = parse_arg()

var.start_time = datetime.now()
var.cli_env = pathlib.Path(__file__, '../')
var.global_config = read_config('global')
var.personal_configs = read_config('personal')
var.default_personal_config = read_config('default_personal')
var.tasks = []
var.maa_env = pathlib.Path(var.global_config['maa_path'])
var.verbose = verbose

adjust_log_file()

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers(),
                    format='%(asctime)s[%(levelname)s][%(name)s] %(message)s')

if __name__ == '__main__':
    logging.info(f'ArkHelperCLI started up at {var.cli_env}.')
    logging.debug(f'With global config {var.global_config}.')
    logging.debug(f'With personal config {var.personal_configs}.')

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

    except Exception as e:
        logging.error(f"An unexpected error was occured when running: {e}", exc_info=True)
