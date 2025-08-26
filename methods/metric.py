import copy
import numpy as np
from sentence_transformers import SentenceTransformer, util

#
model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")
#

def similarity(str1, str2):
    str1_embedding = model.encode(str1, convert_to_tensor=True)
    str2_embedding = model.encode(str2, convert_to_tensor=True)
    similarity_score = util.pytorch_cos_sim(str2_embedding, str1_embedding)
    return similarity_score if similarity_score < 0.90 else 1


def ground_check(informationmatrix):  # ground truth extraction & self-test
    total_define_argument = 0
    total_transfer_var = 0
    total_function_calling = 0
    total_single_tool = 0
    total_multiple_tool = 0
    total_plan_execution = 0

    def argu_check(func_dict: dict):
        nonlocal total_define_argument, total_transfer_var
        for argu in func_dict["arguments_value"]:
            if argu[1][1]:
                if argu[0] in func_dict["first_defined_arguments"]:
                    total_define_argument += 1
                if argu[0] in func_dict["transfered_arguments"]:
                    total_transfer_var += 1

    for file in informationmatrix:
        steps = list(file.keys())
        if "filepath" in steps:
            if file["filepath"][0] != "missing":
                if file["change_maker"]:
                    total_define_argument += 1
                    total_function_calling += 1
            steps.pop(steps.index("filepath"))
        if "save" in steps and file["save"]:
            total_define_argument += 1
            total_function_calling += 1
            steps.pop(steps.index("save"))
        for step in steps:
            if step in ["pages", "annotation"]:
                continue
            for call in file[step]:
                total_function_calling += 1
                argu_check(call)
                if len(call["tool_callings"]) == 1:
                    total_function_calling += 1
                    total_single_tool += 1
                elif len(call["tool_callings"]) > 1:
                    total_function_calling += len(call["tool_callings"])
                    total_multiple_tool += 1
                for tool in call["tool_callings"]:
                    argu_check(tool)
            if step in ["change_maker", "recorder"]:
                total_plan_execution += len(file[step])

    return [
        total_define_argument,
        total_transfer_var,
        total_function_calling,
        total_single_tool,
        total_multiple_tool,
        total_plan_execution,
    ]


def executable_check(inform_matrix):
    executabe = True
    for file in inform_matrix:
        if not file["filepath"][1]:
            executabe = False
            break
        update_file_check = [x["save_path"][1] for x in file["save"]]
        if update_file_check and not all(update_file_check):
            executabe = False
            break
        steps = list(file.keys())
        for step in steps:
            if step in ["filepath", "save", "pages", "annotation"]:
                continue
            for call in file[step]:
                argu_check = [
                    False if x[1][0] and not x[1][1] else True
                    for x in call["arguments_value"]
                ]
                if not all(argu_check):
                    executabe = False
                    break
                for tool in call["tool_callings"]:
                    if tool["arguments_value"]:
                        tool_argu_check = [
                            False if x[1][0] and not x[1][1] else True
                            for x in tool["arguments_value"]
                        ]
                        if not any(tool_argu_check):
                            executabe = False
                            break
    return executabe


def cross_check(groundtruth: list, reaction: list, mode: str):
    totalcount = ground_check(groundtruth)
    execute_score = 30 if executable_check(reaction) else 0

    task_detail_score, totalcount = file_compare(
        groundtruth, totalcount, reaction, mode
    )
    task_score = [
        max(x / y, 0) if y > 0 else 1 for x, y in zip(task_detail_score, totalcount)
    ]
    final_score = execute_score + sum(task_score) * 70 / 6
    return final_score, task_detail_score, totalcount


def file_compare(groundtruth: list, totalcount: list, reaction: list, mode: str):
    sub_task_details = np.zeros(6)
    ground_list = copy.deepcopy(groundtruth)
    react_list = copy.deepcopy(reaction)
    for file in ground_list:
        possible_score = []
        score_details = []
        steps = list(file.keys())
        temp_totalcount = []
        if react_list:
            for pre_file in react_list:
                sub_task_score = np.zeros(6)
                if pre_file["change_maker"]:
                    if (
                        pre_file["filepath"] == file["filepath"]
                        and file["filepath"][0] != "missing"
                    ):
                        sub_task_score[0] += 1
                    if pre_file["filepath"][1] and pre_file["filepath"][0] != "missing":
                        sub_task_score[2] += 1
                if file["save"]:
                    save_value = [
                        (
                            True
                            if x
                            and x["save_path"][0] == file["save"][0]["save_path"][0]
                            else False
                        )
                        for x in pre_file["save"]
                    ]
                    if any(save_value):
                        sub_task_score[0] += 1
                    save_validity = [x["save_path"][1] for x in file["save"]]
                    sub_task_score[2] += min(save_validity.count(True), 1)
                    sub_task_score[2] -= save_validity.count(False)
                else:
                    save_value = [True if x else None for x in pre_file["save"]]
                    if any(save_value):
                        sub_task_score[0] -= len(save_value)
                        sub_task_score[2] -= len(save_value)
                for step in steps:
                    if step in ["filepath", "save", "pages", "annotation"]:
                        continue
                    sub_task_score += call_compare(
                        file[step], totalcount, pre_file[step], mode
                    )
                delta_task_score, tem_count = plan_compare(
                    file, totalcount, pre_file, mode
                )
                sub_task_score += delta_task_score
                temp_totalcount.append(copy.deepcopy(tem_count))
                comprehensive_score = task_grade(tem_count, list(sub_task_score))
                score_details.append(copy.deepcopy(sub_task_score))
                possible_score.append(copy.deepcopy(comprehensive_score))
            index = possible_score.index(max(possible_score))
            sub_task_details = sub_task_details + score_details[index]
            react_list.pop(index)
            totalcount = temp_totalcount[index]
    if react_list:
        sub_task_details -= ground_check(react_list)
    return sub_task_details, totalcount


def task_grade(totalcount: list, sub_task_score: list):
    scores = [y / x if x != 0 else 1 for x, y in zip(totalcount, sub_task_score)]
    comprehensive_score = sum(scores) * 70 / 6
    return max(comprehensive_score, 0)


def fun_validity_check(call):
    function_validity = True
    if call["arguments_value"]:
        for x in call["arguments_value"]:
            if x[1][0] and not x[1][1]:
                function_validity = False
    return function_validity


def call_compare(ground_sequence, totalcount, pre_sequence, mode):
    ground_list = copy.deepcopy(ground_sequence)
    pre_list = copy.deepcopy(pre_sequence)
    sub_task_details = np.zeros(6)
    if ground_list:
        for ground in ground_list:
            possible_score = []
            score_details = []
            if pre_list:
                for pre in pre_list:
                    sub_task_score = np.zeros(6)
                    for x, y in zip(ground["arguments_value"], pre["arguments_value"]):
                        if x[1][1]:
                            if x[0] == "action":
                                sub_task_score[0] += similarity(x[1][0], y[1][0])
                                argu_value = False
                            elif mode == "precise":
                                argu_value = True if x[1][0] == y[1][0] else False
                            else:
                                if x[0] in ground["vaguly_defined_arguments"]:
                                    argu_value = True if y[1][1] else False
                                else:
                                    argu_value = True if x[1][0] == y[1][0] else False
                            if x[0] in ground["first_defined_arguments"]:
                                sub_task_score[0] += 1 if argu_value else 0
                            if x[0] in ground["transfered_arguments"]:
                                sub_task_score[1] += 1 if argu_value else 0
                        else:
                            if x[0] in ground["first_defined_arguments"]:
                                sub_task_score[0] -= 1 if y[1][0] else 0
                            if x[0] in ground["transfered_arguments"]:
                                sub_task_score[1] += 1 if y[1][0] else 0
                    sub_task_score[2] += 1 if fun_validity_check(pre) else 0
                    sub_task_score += tool_compare(
                        ground["tool_callings"], pre["tool_callings"]
                    )
                    comprehensive_score = task_grade(totalcount, list(sub_task_score))
                    score_details.append(sub_task_score)
                    possible_score.append(comprehensive_score)
                index = possible_score.index(max(possible_score))
                sub_task_details = sub_task_details + score_details[index]
                pre_list.pop(index)
    if pre_list:
        for last_pre in pre_list:
            sub_task_details[2] -= 1
            for argu in last_pre["arguments_value"]:
                if argu[1][1]:
                    if argu[0] in last_pre["first_defined_arguments"]:
                        sub_task_details[0] -= 1
                    if argu[0] in last_pre["transfered_arguments"]:
                        sub_task_details[1] -= 1
            if len(last_pre["tool_callings"]) == 1:
                sub_task_details[2] -= 1
                sub_task_details[3] -= 1
            elif len(last_pre["tool_callings"]) > 1:
                sub_task_details[2] -= len(last_pre["tool_callings"])
                sub_task_details[4] -= 1
    return sub_task_details


def tool_compare(ground_tool: list, pre_tool: list):
    ground_list = copy.deepcopy(ground_tool)
    pre_list = copy.deepcopy(pre_tool)
    sub_task_details = np.zeros(6)
    if len(ground_list) == 1:
        if len(pre_list) == 1:
            sub_task_details[3] += (
                1 if ground_list[0]["tool_name"] == pre_list[0]["tool_name"] else 0
            )
            if ground_list[0]["arguments_value"]:
                for arg in ground_list[0]["arguments_value"]:
                    if arg[1][1] and arg in pre_list[0]["arguments_value"]:
                        sub_task_details[0] += 1
            sub_task_details[2] += 1 if fun_validity_check(pre_list[0]) else 0
        else:
            if ground_list[0] in pre_list:
                if ground_list[0]["arguments_value"]:
                    for arg in ground_list[0]["arguments_value"]:
                        if arg[1][1]:
                            sub_task_details[0] += 1
                pre_list.pop(pre_list.index(ground_list[0]))
            sub_task_details[2] -= len(pre_list)
    else:
        if ground_list:
            ground_tool_name = [x["tool_name"] for x in ground_list]
            pre_tool_name = [x["tool_name"] for x in pre_list]
            if ground_tool_name == pre_tool_name:
                sub_task_details[4] += 1
        for ground in ground_list:
            if ground in pre_list:
                if ground["arguments_value"]:
                    for arg in ground["arguments_value"]:
                        if arg[1][1]:
                            sub_task_details[0] += 1
        validity_tool_calling = [fun_validity_check(x) for x in pre_list]
        sub_task_details[2] += min(validity_tool_calling.count(True), len(ground_list))
        sub_task_details[2] -= max(
            validity_tool_calling.count(True) - len(ground_list), 0
        )
    return sub_task_details


def plan_compare(file: dict, totalcount: list, pre_file: dict, mode: str):
    ground_change_maker = copy.deepcopy(file["change_maker"])
    ground_post_maker = copy.deepcopy(file["post_change_maker"])
    pre_change_maker = copy.deepcopy(pre_file["change_maker"])
    pre_post_maker = copy.deepcopy(pre_file["post_change_maker"])
    ground_recorder = copy.deepcopy(file["recorder"])
    pre_recorder = copy.deepcopy(pre_file["recorder"])
    sub_task_details = np.zeros(6)
    if len(pre_change_maker) > len(ground_change_maker):
        totalcount[5] += len(pre_change_maker) - len(ground_change_maker)
    if len(pre_recorder) > len(ground_recorder):
        totalcount[5] += len(pre_recorder) - len(ground_recorder)

    def estimate_plan(ground_list, pre_list, is_recorder=False):
        for ground in ground_list:
            if pre_list:
                for pre in pre_list:
                    plan_check = True
                    for x, y in zip(ground["arguments_value"], pre["arguments_value"]):
                        if mode == "precise":
                            if x[1][0] != y[1][0]:
                                plan_check = False
                                break
                        else:
                            if x[0] in ground["vaguly_defined_arguments"]:
                                if x[1][1] != y[1][1]:
                                    plan_check = False
                                    break
                            else:
                                if x[1][0] != y[1][0]:
                                    plan_check = False
                                    break
                    if ground["tool_callings"] != pre["tool_callings"]:
                        plan_check = False
                    if plan_check:
                        sub_task_details[5] += 0.5 if not is_recorder else 1
                        pre_list.pop(pre_list.index(pre))
                        break
        return pre_list

    if ground_change_maker:
        estimate_plan(ground_change_maker, pre_change_maker)
    if ground_post_maker:
        pre_post_maker = estimate_plan(ground_post_maker, pre_post_maker)
    post_count = len(ground_change_maker) - len(ground_post_maker)
    sub_task_details[5] += max((post_count - len(pre_post_maker)), 0) * 0.5
    if ground_recorder:
        estimate_plan(ground_recorder, pre_recorder, True)
    return sub_task_details, totalcount
