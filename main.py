import time

import Agents.worker_agent as worker_agent
import collections


def main_1():
    print("\033[96m\033[1m" + "\n*****HOO HOO... How may I help you?*****\n" + "\033[0m\033[0m")
    OBJECTIVE = "Find me three recent peer reviewed research papers on the potential of ai to displace workers, and summarize the findings into a report no less than 500 words long"
    task_list = worker_agent.create_task_list(OBJECTIVE)
    worker_agent.print_task_list()
    tasks_completed = []
    # TODO length of task list never changes with the list implementation. if were going to be 'popping' the tasks off a queue,
    #  we need to store the output somehow until the end of the programs run,
    #  because it will need the output for using them as dependent tasks in later primary tasks
    while len(tasks_completed) < len(task_list):
        for task in task_list:
            if task["status"] != "complete":
                worker_agent.execute_task(task, task_list, OBJECTIVE)
                worker_agent.print_task_list()
                print(worker_agent.token_count)
                tasks_completed.append(task)
                break



#
# def main_2():
#     print("\033[96m\033[1m"+"\n*****HOO HOO... How may I help you?*****\n"+"\033[0m\033[0m")
#     OBJECTIVE = input()
#     task_list = collections.deque()
#     task_list = worker_agent.create_task_list()
#     pass


if __name__ == '__main__':
    start = time.time()
    main_1()
