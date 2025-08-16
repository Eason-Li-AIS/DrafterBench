import sys
import os
import re
import signal
import copy

sys.path.append(os.path.abspath(".."))

from DrafterBench.utils.types import Score_builder
from DrafterBench.utils import testf


def timeout_handler(signum, frame):
    raise TimeoutError("Code execution timed out.")


def execute_code(code_string):
    try:
        testf.functions.taskinformation.clear()
        variables = {}
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        exec(code_string, variables)
        signal.alarm(0)
        code_information = copy.deepcopy(variables["testf"].functions.taskinformation)
    except Exception as e:
        code_information = []
    return code_information


def process_code(pre_code):
    test_code = re.sub(
        "import PDFbf|import fitz",
        "from DrafterBench.utils import testf",
        pre_code,
    )
    test_code = re.sub("PDFbf|fitz", "testf", test_code)
    return test_code


def collect_result(
    code_quality: Score_builder,
):
    return {
        "Task_score": {
            "Task_score": code_quality.total_score,
            "Success_arguments_define": code_quality.arguments_count,
            "Total_arguments_define": code_quality.total_arguments,
            "Success_variable_transfer": code_quality.variables_transfer_count,
            "Total_variable_transfer": code_quality.total_variables_transfer,
            "Success_function_calling": code_quality.function_calls_count,
            "Total_function_calling": code_quality.total_function_calls,
            "Success_single_tool_selection": code_quality.single_tool_calls_count,
            "Total_single_tool_selection": code_quality.total_single_tool_calls,
            "Success_multi_tool_selection": code_quality.multi_tool_calls_count,
            "Total_multi_tool_selection": code_quality.total_multi_tool_calls,
            "Intersected_plan_execution": code_quality.intersected_plan_count,
            "Total_plans_appeared": code_quality.all_plan,
            "Ground_plan_execution": code_quality.total_plan_execution,
        },
    }
