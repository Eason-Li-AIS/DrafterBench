# -*- coding: utf-8 -*-
import json
import sys
import os

sys.path.append(os.path.abspath(".."))

from DrafterBench.methods import metric
from DrafterBench.utils.types import Score_builder
from DrafterBench.methods.collect_result import collect_result, process_code, execute_code

def openfile(file):
    f = open(file, "r", encoding="utf-8")
    content = json.load(f)
    return content


def savedate(data, jsonpath):
    with open(jsonpath, "w", encoding="utf-8") as w:
        json.dump(data, w, ensure_ascii=False, indent=4)


def evaluator(result_path, eval_result, response_result):
    test_code = response_result["Response_code"]
    test_code = process_code(test_code)
    test_info = execute_code(test_code)
    ground_code = response_result["Groundtruth"]
    ground_code = process_code(ground_code)
    ground_info = execute_code(ground_code)
    ground_details = metric.ground_check(ground_info)
    prompt_score = (
        Score_builder()
        .ground_fill(ground_details)
        .result(
            *metric.cross_check(
                ground_info,
                test_info,
                (
                    "precise"
                    if response_result["Precise|Vague"] == "Precise"
                    else "vaguely"
                ),
            )
        )
        if test_info
        else Score_builder().ground_fill(ground_details).fail()
    )
    response_result.update(collect_result(prompt_score))
    eval_result.append(response_result)
    eval_data = list(eval_result)
    savedate(eval_data, result_path.replace(".json", "_score.json"))
    return eval_result
