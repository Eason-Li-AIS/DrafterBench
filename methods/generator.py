# -*- coding: utf-8 -*-
import json
import copy
import sys
import os

sys.path.append(os.path.abspath(".."))

from DrafterBench.methods import task_sets
from DrafterBench.methods.agent import Drafter_agent
from DrafterBench.prompts.prompt import Prompt


def openfile(file):
    f = open(file, "r", encoding="utf-8")
    content = json.load(f)
    return content


def savedate(data, jsonpath):
    with open(jsonpath, "w", encoding="utf-8") as w:
        json.dump(data, w, indent=4)


def generator(model, model_provider, temperature, vllm_url, max_length, response_results, result_path, task):
    if len(response_results) <= max_length:
        agent = Drafter_agent(
            model, model_provider, temperature, vllm_url
        )
        indx = task_sets.index(task["Tasktype"]) + 1
        prompt = Prompt(str(indx), task["Instruction"])
        pre_code = agent.get_response(messages=prompt.message())
        ground_code = task["Groundtruth"]
        response = copy.deepcopy(task)
        response.update({"Response_code": pre_code})
        response_results.append(copy.deepcopy(response))
        savedate(list(response_results), result_path)
    return response_results
