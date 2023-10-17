import time


def run_personal_scht_tasks(asst, global_config, config):
    asst.append_task('StartUp', {
        "enable": True,
        "client_type": config.get("client_type", 'Official'),
        "start_game_enabled": True,
        "account_name": config.get("account_name", '')
    })
    # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
    if config.get("account_name", '') != '':
        asst.append_task('StartUp', {
            "enable": True,
            "client_type": config.get("client_type", 'Official'),
            "start_game_enabled": True,
            "account_name": ''
        })
    asst.append_task('Fight', {
        'enable': True,
        'stage': config.get('stage', ''),
        'medicine': 0,
        'expiring_medicine': 0,
        'stone': 0,
        'times': 2147483647,
        'drops': {},
        'report_to_penguin': False,
        'penguin_id': '',
        'server': 'CN',
        'client_type': '',
        'DrGrandet': False
    })
    asst.append_task('Infrast', {
        'facility': [
            'Mfg',
            'Trade',
            'Control',
            'Power',
            'Reception',
            'Office',
            'Dorm',
            'Processing'
        ],
        'drones': config.get('drones', 'PureGold'),
        'threshold': 0.2,
        'dorm_notstationed_enabled': True,
        'dorm_trust_enabled': True,
        'replenish': True,
        'mode': 0,
        'filename': '',
        'plan_index': 0
    })
    asst.append_task('Recruit', {
        'refresh': True,
        'force_refresh': True,
        'select': [
            4
        ],
        'confirm': [
            3,
            4
        ],
        'times': 3,
        'set_time': True,
        'expedite': False,
        'expedite_times': 3,
        'skip_robot': True,
        'recruitment_time': {
            '3': 460
        },
        'report_to_penguin': True,
        'report_to_yituliu': True,
        'penguin_id': '',
        'server': 'CN'
    })
    asst.append_task('Mall', {
        'credit_fight': False,
        'shopping': True,
        'buy_first': [
            '招聘许可',
            '赤金'
        ],
        'blacklist': [
            '加急许可'
        ],
        'force_shopping_if_credit_full': True
    })
    asst.append_task('Award', {
        'award': True,
        'mail': True
    })

    asst.start()

    while asst.running():
        time.sleep(1)
