import json
import logging
from typing import Dict, List
import openai
from serpapi import GoogleSearch
import Constants.settings as settings
from Tools.web_search_tool import web_search_tool
"""THIS AGENT IS THE MAIN WORKER OF THE PROGRAM. IT CREATES A TASK LIST BASED ON THE INITIAL USER PROMPT,
 IN AN ATTEMPT TO RESEARCH THE PROBLEM AND RETURN RELEVANT INFORMATION. IT THEN EX"""
# todo maybe a deque would work better than a list
OBJECTIVE = None
task_list = []
serpapi_key = settings.SERPAPI_KEY
# Configure OpenAI and SerpAPI client
openai.api_key = settings.OPEN_AI_API_KEY
if serpapi_key:
    serpapi_client = GoogleSearch({"api_key": serpapi_key})
    websearch_var = "[web-search] "
else:
    websearch_var = ""


def create_task_list(objective: str) -> List[Dict]:
    OBJECTIVE = objective
    global task_list
    condensed_tasks = [{k: v for k, v in task.items() if k != "result"} for task in
                       task_list]  # this line extracts relevant info from the task list to pass as context
    # set prompt
    prompt = (
        f"You are a task creation AI tasked with creating a list of tasks as a JSON array, considering the ultimate objective of your team: {OBJECTIVE}. "
        f"Create new tasks based on the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed."
        f"Current tool option is [text-completion] and {websearch_var} only."  # web-search is added automatically if SERPAPI exists
        f"For tasks using [web-search], provide the search query, and only the search query to use (eg. not 'research waterproof shoes, but 'waterproof shoes')"
        f"dependent_task_ids should always be an empty array, or an array of numbers representing the task ID it should pull results from."
        f"Make sure all task IDs are in chronological order.\n"
        f"The last step is always to provide a final summary report including tasks executed and summary of knowledge acquired.\n"
        f"Do not create any summarizing steps outside of the last step..\n"
        f"An example of the desired output format is: "
        "[{\"id\": 1,"
        " \"task\": \"https://untapped.vc\","
        " \"tool\": \"web-scrape\","
        " \"dependent_task_ids\": [],"
        " \"status\": \"incomplete\","
        " \"result\": null,"
        " \"result_summary\": null},"
        " {\"id\": 2,"
        " \"task\": \"Consider additional insights that can be reasoned from the results of...\","
        " \"tool\": \"text-completion\","
        " \"dependent_task_ids\": [1],"
        " \"status\": \"incomplete\","
        " \"result\": null,"
        " \"result_summary\": null},"
        " {\"id\": 3,"
        " \"task\": \"Untapped Capital\","
        " \"tool\": \"web-search\","
        " \"dependent_task_ids\": [],"
        " \"status\": \"incomplete\","
        " \"result\": null,"
        " \"result_summary\": null}].\n"
        f"JSON TASK LIST="
    )

   # log statements
    print("\033[90m\033[3m" + "\nInitializing...\n" + "\033[0m")
    print("\033[90m\033[3m" + "Analyzing objective...\n" + "\033[0m")
    print("\033[90m\033[3m" + "Running task creation agent...\n" + "\033[0m")

    # todo replace with better api call
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a task creation AI."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=2000,
        n=1,
        stop="###",
        temperature=0.5,
    )

    result = response["choices"][0]["message"]["content"]
    try:
        task_list = json.loads(result)
    except Exception as err:
        logging.error(str(err))

    return task_list


def execute_task(task: Dict, task_list: List, OBJECTIVE: str):
    task_output = None
    # Check if dependent_task_ids is not empty
    if task["dependent_task_ids"]:  # if there are any dependencies...
        all_dependent_tasks_complete = True  # start with all tasks completed
        for dependent_task_id in task["dependent_task_ids"]:  # loop through dependency tasks
            dependent_task = get_task_by_id(dependent_task_id)
            if not dependent_task or dependent_task["status"] != "complete":  # if the task is NOT complete
                all_dependent_tasks_complete = False  # change the tasks complete flag back to false
                break

    # Execute task
    print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
    print(str(task['id']) + ": " + str(task['task']) + " [" + str(task['tool'] + "]"))
    task_prompt = f"Complete your assigned task based on the objective " \
                  f"and based on information " \
                  f"provided in the dependent task output, if dependent task output is provided." \
                  f" Your objective: {OBJECTIVE}. Your task: {task['task']}"
    if task["dependent_task_ids"]:  # if the task has dependent tasks
        dependent_tasks_output = ""
        for dependent_task_id in task["dependent_task_ids"]:  # loop through their ids
            dependent_task_output = get_task_by_id(dependent_task_id)["output"]
            # dependent_task_output = dependent_task_output["choices"][0]["message"]["content"]
            print(dependent_task_output)# find the tasks output and save it
            dependent_task_output = dependent_task_output[0:2000]  # clip it to size
            dependent_tasks_output += f" {dependent_task_output}"  # append the dependency task outputs together
        task_prompt += f" Your dependent tasks output: {dependent_tasks_output}\n OUTPUT:"  # append the outputs to the prompt context

    # Use tool to complete the task
    # todo this is rudimentary we can use a routing chain for this
    if task["tool"] == "text-completion":
        task_output = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {   # todo this prompt should be rewritten and benchmarked against the original.
                    "role": "system",
                    "content": "You are a task creation AI."
                },
                {
                    "role": "user",
                    "content": task_prompt
                }
            ],
            max_tokens=2000,
            n=1,
            stop="###",
            temperature=0.5,
        )
        task_output = task_output["choices"][0]["message"]["content"]
        # text_completion_tool(task_prompt)
    elif task["tool"] == "web-search":
        # TODO there needs to be a function that uses an llm call to convert the task into a valid search query
        task_output = web_search_tool(str(task['task']))
    # Find task index in the task_list
    task_index = None
    for i, t in enumerate(task_list):
        if t["id"] == task["id"]:
            task_index = i
            break

    # Mark task as complete and save output
    task_list[task_index]["status"] = "complete"
    task_list[task_index]["output"] = task_output
    # todo save prompt and output to chroma db
    # Print task output
    print("\033[93m\033[1m" + "\nTask Output:" + "\033[0m\033[0m")
    print(task_output)
    # print(task_output["choices"][0]["message"]["content"])

    # # Add task output to session_summary
    # global session_summary
    # session_summary += f"\n\nTask {task['id']} - {task['task']}:\n{task_output}"


def get_task_by_id(id: int) -> Dict:
    for task in task_list:
        if task["id"] == id:
            return task


def add_task(task: Dict):
    task_list.append(task)


def get_completed_tasks():
    return [task for task in task_list if task["status"] == "complete"]


def get_objective() -> str:
    return OBJECTIVE


# Print task list and session summary
def print_task_list():
    print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m")
    for t in task_list:
        dependent_task = ""
        if t['dependent_task_ids']:
            dependent_task = f"\033[31m<dependencies: {', '.join([f'#{dep_id}' for dep_id in t['dependent_task_ids']])}>\033[0m"
        status_color = "\033[32m" if t['status'] == "complete" else "\033[31m"
        print(
            f"\033[1m{t['id']}\033[0m: {t['task']} {status_color}[{t['status']}]\033[0m \033[93m[{t['tool']}] {dependent_task}\033[0m")
