from Libs.utils import *


def choice_stage(server, preference_stage: dict):
    stages_in_limit_list = [cp for cp in preference_stage if cp.rsplit('-', 1)[0] in arknights_stage_opening_time]
    stages_outof_limit_list = [cp for cp in preference_stage if not cp.rsplit('-', 1)[0] in arknights_stage_opening_time]

    for stage in stages_in_limit_list:
        opening_time = arknights_stage_opening_time[stage.rsplit('-', 1)[0]]

        if in_game_week(datetime.now(), server) not in opening_time:
            preference_stage.pop(stage)
            continue

        rate_standard_coefficient = len(opening_time)
        preference_stage[stage] /= rate_standard_coefficient  # 平衡概率

    for stage in stages_outof_limit_list:
        preference_stage[stage] /= 7  # 平衡概率

    return random_choice_with_weights(preference_stage)
