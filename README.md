# :wrench: DrafterBench
This repository is the official implementation of DrafterBench. We provide evaluation data, codes, and a brief introduction.

![Static Badge](https://img.shields.io/badge/Code_License-MIT_License-blue) ![Static Badge](https://img.shields.io/badge/Linux_%2F_OSX-Passing-green) ![Static Badge](https://img.shields.io/badge/Window-Failing-red) ![Static Badge](https://img.shields.io/badge/python-3.11-purple)


---

## :star: Introducing DrafterBench

The DrafterBench is designed to evaluate large language models (LLMs) as an agent to automate monotonous, low-tech, and high-labor-intensity tasks in industry. Our initiative is drawing revision, which is a representation task in civil engineering that urgently needs to be automated. We took the following workflow to simulate the working scenario and evaluate the strengths and limitations of LLMs as automation agents.

![Automation Workflow](/figures/Workflow.png "Automation Workflow")

After the stage of preprocessing, the drawing revision tasks (summarized from the real world, totalling 1920 across 12 types) are converted into natural language processing (NLP) tasks to evaluate complex function calls instructed by intricate and lengthy content commands. We designed over 40 drawing revision tools and provided them to LLMs, which play different functions. Some of them aim to make visible changes to drawings, while the others serve necessary preparations for them (e.g., opening the file or transferring critical arguments). It's difficult to determine whether the tools called are effective and functioning properly from the revised drawings, especially when checking if there are redundant or duplicated invisible tools. Therefore, to accurately evaluate the models‘ performance, we score their responses based on the operation chains rather than the revised drawing results.

To record the operation chains, we prepared dual functions for the tools provided to the LLMs. Each dual function has the same name, input, and output type as the original tools, and its function is to capture the operations and valuable data in a well-structured JSON format (e.g., argument value, data type, etc.). During the working of the benchmark, the original tools called by the models will be replaced with dual functions to record the operation chains and help the final assessment.

There are four essential capabilities evaluated by DrafterBench:
- **Structured data understanding**
- **Function execution**
- **Instruction following**
- **Critical reasoning**

![Capabilities Illustration](/figures/Capabilities.png "Capabilities Illustration")

## :ski: Table of Contents

- [Dataset Summary](#dataset-summary)
- [Quick Start](#quick-start)
- [LeaderBoard](#leaderboard)

---

## :clipboard: <span id="dataset-summary">Dataset Summary</span>

The DrafterBench is constructed on tasks over three object elements, four operations, and six complexity controllers.

| Elements         | Operations              | Complexity Controllers                       | Capacities Investigated by Various Complexity         |
|------------------|-------------------------|----------------------------------------------|-------------------------------------------------------|
| Text             | Add new content         |Language style (Structured/Unstructured)      |Structured data understanding                          |
| Table            | Revise content          |Task categories                               |Function execution                                     |
| Vector entity    | Change position         |Objects per instruction (Single/Multiple)     |Instruction following                                  |
|                  | Update format           |Operations per object (Single/Multiple)       |Instruction following                                  |
|                  |                         |Instruction completeness (Complete/Incomplete)|Critical reasoning                                     |
|                  |                         |Detail ambiguity (Precise/Vague)              |Critical reasoning                                     |

The dataset is [available here](https://huggingface.co/datasets/Eason666/DrafterBenchmark) on Huggingface.

## :fire: <span id="quick-start">Quick Start</span>

### Preparation

First, configure an environment with Python 3.11 and download the repositories.

```shell
git clone https://github.com/Eason-Li-AIS/DrafterBench.git
cd DrafterBench
```

Then, install the dependencies.

```shell
pip install -e .
```

### Serve Model
- For API calling, set up your OpenAI / Anthropic / Google / Mistral / Deepinfra / AnyScale or other API keys as environment variables.

    ```shell
    OPENAI_API_KEY=...
    ANTHROPIC_API_KEY=...
    GOOGLE_API_KEY=...
    MISTRAL_API_KEY=...
    DEEPINFRA_API_KEY=...
    HUGGINGFACE_TOKEN=...
    ```
- For customized model, provide your vllm url when running evaluation.py

    ```shell
    --vllm_url http://xx.xx.xx.xx:8000/v1
    ```

### Run evaluation
Specify the --model and --model-provider flags to run DrafterBench. The supported models and providers are [available here](https://docs.litellm.ai/docs/providers). You can name your experiment with the --exp_name flag, or it will be set as "model+time+task_group" by default.
```shell
python evaluation.py --model gpt-4o-2024-08-06 --model-provider openai --temperature 0.0
```

- To run tasks of a specific set, use the --task_group flag. You can choose each set in ["Structured", "Unstructured", "Precise", "Vague", "Complete", "Error", "Single_Object", "Multiple_Objects", "Single_Operation", "Multiple_Operations"]. For example:

  ```shell
  python evaluation.py --model gpt-4o-2024-08-06 --model-provider openai --task_group Structured
  ```
  This command will run only the tasks in a structured language. The default task group is "All" tasks.

- To have a clear view of the result, you can set up your huggingface token, 
  ```shell
   HUGGINGFACE_TOKEN=...
  ```
  then use the --huggingface_user_name flag to provide your Huggingface user name. Our benchmark will create a new dataset repository with the --exp_name and push the results to it. This repository is private by default, you can create a public repository by setting the --huggingface_private flag to False.
  ```shell
  python evaluation.py --model gpt-4o-2024-08-06 --model-provider openai --task_group Structured --huggingface_user_name XXXXX(Replace "XXXXX" with your Huggingface username)
  ```
- The default prompts for 12 tasks can be found in ./prompts. You are encouraged to develop your own prompts to achieve a higher score. To do so, simply replace the default prompts in .txt file with your new prompts.

## :mortar_board: <span id="leaderboard">LeaderBoard</span>

|Metric|o3-2025-04-16 (Mean/Var)|o4-mini-2025-04-16 (Mean/Var)|gpt-4.1-2025-0414 (Mean/Var)|gpt-4o-mini (Mean/Var)|o1-2024-12-17 (Mean/Var)|gpt-4o-2024-08-06 (Mean / Var)|claude-3.5-sonnet-2024-1022 (Mean / Var)|DeepSeek-V3-0324 (Mean / Var)|Qwen2.5-72B-Instruct (Mean / Var)|LLaMA3-70B-Instruct (Mean / Var)|
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
|Structured language|85\.90/0.10|79\.99/0.44|79\.96/0.84|69\.22/0.02|80\.26/1.33|74\.95/1.85|74\.69/0.95|74\.52/0.70|73\.04/1.09|68\.82/2.36|
|Unstructured language|86\.16/0.03|79\.87/0.07|80\.36/0.87|69\.24/0.02|80\.73/1.77|74\.95/2.04|76\.70/1.68|74\.51/0.25|72\.67/0.14|68\.23/2.03|
|Precise detail|91\.27/0.01|88\.36/0.21|87\.07/0.49|73\.90/0.01|89\.86/0.40|80\.63/4.07|82\.75/1.99|78\.24/0.17|75\.03/0.05|71\.33/4.34|
|Vague detail|80\.79/0.13|71\.50/0.37|73\.25/1.33|64\.57/0.02|70\.45/1.84|69\.27/0.55|69\.64/2.84|70\.79/0.58|70\.66/0.70|65\.68/0.93|
|Complete instruction|87\.76/0.15|80\.14/0.66|81\.68/1.06|72\.70/0.04|79\.01/2.92|80\.06/1.99|84\.78/0.86|86\.16/0.79|87\.44/0.57|83\.64/5.82|
|Incomplete (error) instruction|84\.31/0.07|79\.72/0.09|78\.64/0.74|65\.76/0.10|81\.97/0.59|71\.01/6.98|66\.86/2.91|62\.87/3.06|58\.26/0.49|53\.41/0.27|
|Single object|87\.02/0.02|81\.07/0.31|80\.98/0.13|69\.79/0.02|81\.83/1.48|74\.53/6.06|73\.81/1.04|74\.05/0.73|73\.30/0.46|67\.28/2.97|
|Multiple objects|85\.04/0.14|78\.79/0.06|79\.34/2.19|68\.67/0.14|79\.15/1.60|75\.37/0.20|78\.10/0.21|74\.98/0.52|72\.41/0.06|69\.77/1.31|
|Single operation|86\.11/0.06|80\.01/0.20|81\.80/0.62|69\.88/0.01|81\.35/0.91|75\.79/1.91|75\.91/0.91|76\.73/0.15|75\.16/0.27|70\.85/2.17|
|Multiple operations|85\.84/0.07|79\.75/0.69|76\.17/1.57|67\.66/0.14|78\.14/2.17|73\.00/1.81|75\.41/0.20|69\.33/2.69|67\.53/1.18|63\.14/1.75|
|Average tasks|86\.03/0.05|79\.93/0.15|80\.16/0.85|69\.23/0.01|80\.49/1.53|74\.95/1.81|75\.85/0.36|74\.69/0.83|72\.85/0.16|68\.52/2.02|
|Comprehensive rewards|84\.04/0.05|76\.80/0.23|77\.88/1.09|65\.42/0.02|78\.06/2.55|72\.24/2.33|73\.39/0.45|71\.74/0.81|69\.94/0.20|64\.96/2.44|

Note: We have recently upgraded DrafterBench to be more challenging. Although the trend of models' ability is very consistent with the above leaderboard, some models may score lower than the records.
The score on the leaderboard is the average of three independent runs.

## Citation

If you use DrafterBench in your research, please consider citing our paper:

```bibtex
@article{drafterbench,
  title={DrafterBenchmark: Benchmarking Large Language Models for Tasks Automation in Civil Engineering},
  author={Yinsheng Li, Zhen Dong, Yi Shao.},
  year={2025},
  url={https://arxiv.org/abs/2507.11527},
}
