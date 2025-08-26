# -*- coding: utf-8 -*-
import copy
import multiprocessing
import numpy as np
import datetime
import sys
import os
import json
import glob
from tqdm import tqdm
from functools import partial
from datasets import DatasetDict, Dataset, load_dataset
from multiprocessing import Manager, Lock
from . import task_sets

sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../.."))

from DrafterBench.methods.generator import generator

def score_format(da):
    def calculate_score(success_count, total_count):
        return success_count / total_count if total_count else 1

    format = {
        "Tasktype": da["Tasktype"],
        "Task_id": da["Id"],
        "Define_arguments": calculate_score(
            da["Task_score"]["Success_arguments_define"],
            da["Task_score"]["Total_arguments_define"],
        ),
        "Transfer_variable": calculate_score(
            da["Task_score"]["Success_variable_transfer"],
            da["Task_score"]["Total_variable_transfer"],
        ),
        "Call_function": calculate_score(
            da["Task_score"]["Success_function_calling"],
            da["Task_score"]["Total_function_calling"],
        ),
        "Single_tool": calculate_score(
            da["Task_score"]["Success_single_tool_selection"],
            da["Task_score"]["Total_single_tool_selection"],
        ),
        "Multi-tool": calculate_score(
            da["Task_score"]["Success_multi_tool_selection"],
            da["Task_score"]["Total_multi_tool_selection"],
        ),
        "Execute_plan": calculate_score(
            da["Task_score"]["Intersected_plan_execution"],
            da["Task_score"]["Total_plans_appeared"],
        ),
        "Task_score": da["Task_score"]["Task_score"],
    }
    return format


def evaluate(args):
    print(f"The benchmark is runing with following arguments:")
    print(f"{args}")
    print(f"Running tasks in {args.task_group} set(s)")
    os.makedirs(f"{args.result_dir}/{args.model.replace('/', '_')}", exist_ok=True)
    if args.exp_name == "default_name":
        args.exp_name = f"{args.model.replace('/', '_')}_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}_{args.task_group}"
    

    response_results = Manager().list()
    max_length = 1920
    resume_path = None
    if args.resume_from:
        resume_path = args.resume_from
    elif args.auto_resume:
        result_dir = f"{args.result_dir}/{args.model.replace('/', '_')}"
        pattern = os.path.join(result_dir, f"*_{args.task_group}.json")
        files = glob.glob(pattern)
        if not files:
            print("No saved results found in {{args.result_dir}/{args.model.replace('/', '_')}}")
            user_input = input("Would you like to run a new assessment? (Yes/No):")
            if user_input == "Yes":
                print("Run a new assessment")
                result_path = f"{args.result_dir}/{args.model.replace('/', '_')}/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}_{args.task_group}.json"
            else:
                print("Stop running DrafterBench")
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        resume_path = files[0]
        print(f"Find existing results archive: {resume_path}")
    else:
        result_path = f"{args.result_dir}/{args.model.replace('/', '_')}/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}_{args.task_group}.json"
    
    if resume_path:
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                results_saved = json.load(f)
        except Expection as e:
            print(f"[Error] Faile to load saved results: {e}")
            return
        response_results.extend(results_saved)
        result_path = resume_path
        print(f"Resumed {len(results_saved)} items from {resume_path} ...")

    task_messages = load_dataset("Eason666/DrafterBench", "drafter_tasks")
    specified_instructions = []
    for task_set in task_sets:
        if args.debug:
            specified_instructions.extend(
                [task_messages[task_set][i] for i in [1, 2, 3]]
            )
        else:
            if args.task_group == "All":
                specified_instructions.extend(
                    [
                        task_messages[task_set][i]
                        for i in range(len(task_messages[task_set]))
                    ]
                )
            else:
                for i in range(len(task_messages[task_set])):
                    task_parameters = [
                        task_messages[task_set][i]["Precise|Vague"],
                        task_messages[task_set][i]["Complete|Incomplete"],
                        task_messages[task_set][i]["Single|Multiple_objects"],
                        task_messages[task_set][i]["Single|Multiple_operations"],
                        task_messages[task_set][i]["Structured/Unstructured"],
                    ]
                    if args.task_group in task_parameters:
                        specified_instructions.append(task_messages[task_set][i])
    
    completed_ids = {
        (item["Tasktype"], item["Id"]) for item in response_results
    }
    remaining = len(specified_instructions) - len(completed_ids)
    if not remaining:
        print("[Resume] No remaining tasks. Skipping generation.")
    else:
        print(f"[Gen] Total tasks: {len(specified_instructions)} | Remaining: {remaining}")


    
    ctx = multiprocessing.get_context("spawn")
    if remaining:
        specified_instructions = [
            task for task in specified_instructions
            if (task["Tasktype"], task["Id"]) not in completed_ids
        ]
        pool1 = ctx.Pool(processes=args.proc_num)
        print("Getting agent responses:")
        generator_partial = partial(
            generator, args.model, args.model_provider, args.temperature, args.vllm_url, max_length, response_results, result_path
        )
        r = list(
            tqdm(
                pool1.imap_unordered(generator_partial, specified_instructions),
                total=len(specified_instructions),
            )
        )
        pool1.close()
        pool1.join()

    from DrafterBench.methods.evaluator import evaluator

    eval_results = Manager().list()
    pool2 = ctx.Pool(processes=args.proc_num)
    print("Evaluating agent responses:")
    evaluator_partial = partial(evaluator, result_path, eval_results)
    responses = copy.deepcopy(list(response_results))
    p = list(tqdm(pool2.imap_unordered(evaluator_partial, responses), total=len(responses)))
    pool2.close()
    pool2.join()

    eval_list = list(eval_results)
    task_rewards = {}
    for task in task_sets:
        rewards = [
            x["Task_score"]["Task_score"] for x in eval_list if x["Tasktype"] == task
        ]
        task_rewards.update({task: np.average(rewards)})
    average_task_rewards = np.average([task_rewards[x] for x in task_sets])
    comprehensive_rewards = (
        average_task_rewards - (100 - min([task_rewards[x] for x in task_sets])) / 12
    )
    structured_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Structured/Unstructured"] == "Structured"
    ]
    unstrctured_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Structured/Unstructured"] == "Unstructured"
    ]
    precise_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Precise|Vague"] == "Precise"
    ]
    vague_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Precise|Vague"] == "Vague"
    ]
    complete_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Complete|Incomplete"] == "Complete"
    ]
    error_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Complete|Incomplete"] == "Error"
    ]
    single_OB_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Single|Multiple_objects"] == "Single_Object"
    ]
    multiple_OB_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Single|Multiple_objects"] == "Multiple_Objects"
    ]
    single_OP_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Single|Multiple_operations"] == "Single_Operation"
    ]
    multiple_OP_rewards = [
        x["Task_score"]["Task_score"]
        for x in eval_list
        if x["Single|Multiple_operations"] == "Multiple_Operations"
    ]
    average_structured_rewards = (
        np.average(structured_rewards) if structured_rewards else "NaN"
    )
    average_unstrctured_rewards = (
        np.average(unstrctured_rewards) if unstrctured_rewards else "NaN"
    )
    average_precise_rewards = np.average(precise_rewards) if precise_rewards else "NaN"
    average_vague_rewards = np.average(vague_rewards) if vague_rewards else "NaN"
    average_complete_rewards = (
        np.average(complete_rewards) if complete_rewards else "NaN"
    )
    average_error_rewards = np.average(error_rewards) if error_rewards else "NaN"
    average_single_OB_rewards = (
        np.average(single_OB_rewards) if single_OB_rewards else "NaN"
    )
    average_multiple_OB_rewards = (
        np.average(multiple_OB_rewards) if multiple_OB_rewards else "NaN"
    )
    average_single_OP_rewards = (
        np.average(single_OP_rewards) if single_OP_rewards else "NaN"
    )
    average_multiple_OP_rewards = (
        np.average(multiple_OP_rewards) if multiple_OP_rewards else "NaN"
    )

    reward_matrix = {
        "Structured": f"Structured language: {average_structured_rewards}\n",
        "Unstructured": f"Unstructured language: {average_unstrctured_rewards}\n",
        "Precise": f"Precise detail: {average_precise_rewards}\n",
        "Vague": f"Vague detail: {average_vague_rewards}\n",
        "Complete": f"Completed instruction: {average_complete_rewards}\n",
        "Error": f"Incomplete (error) instruction: {average_error_rewards}\n",
        "Single_Object": f"Single object: {average_single_OB_rewards}\n",
        "Multiple_Objects": f"Multiple objects: {average_multiple_OB_rewards}\n",
        "Single_Operation": f"Single operation: {average_single_OP_rewards}\n",
        "Multiple_Operations": f"Multiple operations: {average_multiple_OP_rewards}\n"
    }

    if args.task_group == 'All':
        print("Average reward in different metrics:\n")
        reward = (
            f"Structured language: {average_structured_rewards}\n"
            f"Unstructured language: {average_unstrctured_rewards}\n"
            f"Precise detail: {average_precise_rewards}\n"
            f"Vague detail: {average_vague_rewards}\n"
            f"Complete instruction: {average_complete_rewards}\n"
            f"Incomplete (error) instruction: {average_error_rewards}\n"
            f"Single object: {average_single_OB_rewards}\n"
            f"Multiple objects: {average_multiple_OB_rewards}\n"
            f"Single operation: {average_single_OP_rewards}\n"
            f"Multiple operations: {average_multiple_OP_rewards}\n"
            f"Average tasks: {average_task_rewards}\n"
            f"Comprehensive rewards: {comprehensive_rewards}"
        )
    else:
        print("Average reward of the task group you specified:\n")
        reward = reward_matrix[args.task_group]
    print(reward)
    text_result_path = f"{args.result_dir}/{args.model.replace('/', '_')}/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}_{args.task_group}.txt"
    with open(text_result_path, "w", encoding="utf-8") as w:
        w.write(reward)
    print(f"The experiment result has been saved in {args.result_dir}.")

    organized_data = [score_format(x) for x in eval_list]
    if args.huggingface_user_name:
        dataset = Dataset.from_list(organized_data)
        dataet_dict = DatasetDict({"result": dataset})
        dataet_dict.push_to_hub(
            f"{args.huggingface_user_name}/{args.exp_name}",
            token=os.getenv("HUGGINGFACE_TOKEN"),
            private=args.huggingface_private,
        )
        print(
            f"Dataset successfully pushed to the hub at https://huggingface.co/{args.huggingface_user_name}/{args.exp_name}"
        )
