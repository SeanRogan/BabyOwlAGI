import Agents.worker_agent as worker_agent

if __name__ == '__main__':

    print("\033[96m\033[1m"+"\n*****HOO HOO... How may i help you?*****\n"+"\033[0m\033[0m")
    #OBJECTIVE = input()
    OBJECTIVE = "Research the industrial revolution and its impacts on society in the colonial americas"
    task_number = 1
    task_list = worker_agent.create_task_list(OBJECTIVE)
    worker_agent.print_task_list()
    while len(task_list) > 0:
        for task in task_list:
            if task["status"] != "complete":
                worker_agent.execute_task(task, task_list, OBJECTIVE)
                worker_agent.print_task_list()
                break
