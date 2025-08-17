import argparse
import os
import time
import sys
from litellm import provider_list
from methods.evaluate import evaluate

sys.path.append(os.path.abspath(".."))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use for the agent",
    )
    parser.add_argument(
        "--model-provider",
        type=str,
        choices=provider_list,
        help="The model provider for the agent",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="The temperature for the agent",
    )
    parser.add_argument("--exp_name", type=str, default=f"default_name")
    parser.add_argument("--result_dir", type=str, default="results/")
    parser.add_argument("--proc_num", type=int, default=16)
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument(
        "--task_group",
        type=str,
        choices=[
            "Structured",
            "Unstructured",
            "Precise",
            "Vague",
            "Complete",
            "Error",
            "Single_Object",
            "Multiple_Objects",
            "Single_Operation",
            "Multiple_Operations",
            "All",
        ],
        default="All",
    )
    parser.add_argument("--huggingface_user_name", type=str, default=None)
    parser.add_argument("--huggingface_private", type=bool, default=True)
    parser.add_argument("--vllm_url", type=str, default=None)
    parser.add_argument("--results_path", type=str, default="")
    args = parser.parse_args()

    return args


def main():
    starttime = time.time()
    args = parse_args()
    evaluate(args)
    endtime = time.time()
    timespan = endtime - starttime
    print(f"Benchmark finsihed in {timespan} s.")


if __name__ == "__main__":
    main()
