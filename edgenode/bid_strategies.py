import operator
from random import choice, sample
from networkx.algorithms.components import *
from networkx.algorithms.traversal import *
# from edgeresprov.fognode.taskresource import make_vector
from taskresource import make_vector

import json
from networkx import DiGraph


def strategy_max_resource_attr(taskgraph, attr):
    """ returns the task id with the max attribute attr """
    snestdict = [(k, max([(k2, v) for k2, v in d.iteritems() if k2 == attr],
                         key=lambda a:a[1])) for k, d in taskgraph.node.iteritems()]
    return [max(snestdict, key=lambda a: a[1][1])[0]]


def strategy_random_resource(taskgraph, FognodeResources):
    """ returns a bid containing tasks to randomly maximize resources"""
    TaskResources = make_vector('ram cpu hdd')
    component_resources = TaskResources(ram=0, cpu=0, hdd=0)
    bid = []
    tasks = taskgraph.nodes()
    for node in taskgraph.nodes():
        selected = choice(tasks)
        if taskgraph.node[selected][1] in FognodeResources[1]:
            component_resources += taskgraph.node[selected][0]
            if component_resources[0] <= FognodeResources[0][0] and component_resources[1] <= FognodeResources[0][1]\
                and component_resources[2] <= FognodeResources[0][2]:
                bid.append(str(selected))
            tasks.remove(selected)
        else:
            tasks.remove(selected)
    return bid


def strategy_strong_components(taskgraph, FognodeResources):
    """ find strongly connected component that can fit. Randomly choose among set of all !!"""
    # strongly connected or diconnected if every vertex is reachable from
    # every other vertex. The strongly connected components or diconnected
    # components of an arbitrary directed graph form a partition into
    # subgraphs that are themselves strongly connected
    # Generate a sorted list of strongly connected components
    # connecteds = list(strongly_connected_components(taskgraph))

    # Generate a sorted list in descendent order based on their length
    connecteds = [c for c in sorted(strongly_connected_components(taskgraph), key=len, reverse=True)]


    # dont loop forever
    # we try to fit as many tasks as possible starting with the largest connected component
    for subgraph in connecteds:
        bid = []
        TaskResources = make_vector('ram cpu hdd')
        component_resources = TaskResources(ram=0, cpu=0, hdd=0)
        for tasknode in subgraph:
            if taskgraph.node[tasknode][1] in FognodeResources[1]:
                component_resources += taskgraph.node[tasknode][0]
                bid.append(tasknode)
            else:
                continue
        if component_resources < FognodeResources[0] and component_resources != TaskResources(ram=0, cpu=0, hdd=0):
            return bid
    return []


def strategy_maximise_coverage_knapsack(taskgraph, FognodeResources):
    """ try to fit as many tasks as possible across the resource dimensions. It is a knapsack problem. """

    capacity = FognodeResources
    items = [(name, taskresource, 1)
             for name, taskresource in taskgraph.node.items()]

    accepted_items = []
    for item in items:
        if item[1][1] in capacity[1]:
            i = (item[0], item[1][0], item[2])
            accepted_items.append(i)
    bagged = knapsack01_dp(accepted_items, capacity[0])
    return [task for task, taskresource[0], times in bagged]


def strategy_max_fanout(taskgraph, FognodeResources):
    """ start from node with the max fanout that can fit. then traverse to include neighbours until
    FognodeResources are depleted """

    bagged = []
    highest = None
    # Sort graph nodes according to their degree
    sorted_nodes = sorted(taskgraph.degree_iter(),
                          key=operator.itemgetter(1), reverse=True)
    for node in [nodename for nodename, noofedges in sorted_nodes]:
        if taskgraph.node[node][0] < FognodeResources[0] and taskgraph.node[node][1] in FognodeResources[1]:
            highest = node
            break
    if highest is None:
        return bagged
    bagged_resources = taskgraph.node[highest][0]
    bagged.append(highest)
    for succ in bfs_successors(taskgraph, highest).keys():
        if (taskgraph.node[succ][0] + bagged_resources) < FognodeResources[0] and \
                taskgraph.node[succ][1] in FognodeResources[1]:
            bagged.append(succ)
            bagged_resources += taskgraph.node[succ][0]
    return bagged


def knapsack01_dp(items, capacity):
    """ 0/1 knapsack dynamic programming style """
    tabledict = {}

    for w in capacity.range(capacity):
        tabledict[w] = [0 for j in xrange(len(items) + 1)]
    for j in xrange(1, len(items) + 1):
        item, wt, val = items[j - 1]
        for w in capacity.range(capacity):
            if wt > w:
                tabledict[w][j] = tabledict[w][j - 1]
            else:
                tabledict[w][j] = max(
                    tabledict[w][j - 1], tabledict[w - wt][j - 1] + val)
    result = []
    TaskResources = make_vector('ram cpu hdd')

    w = capacity - TaskResources(1, 1, 1)
    for j in range(len(items), 0, -1):
        was_added = tabledict[w][j] != tabledict[w][j - 1]

        if was_added:
            item, wt, val = items[j - 1]
            result.append(items[j - 1])
            w -= wt
    return result


if __name__ == '__main__':

    TaskResources = make_vector('ram cpu hdd')
    #
    # items = [
    #     # NAME, TaskResources, VALUE
    #     ('blue', TaskResources(3, 2, 2), 1),
    #     ('red', TaskResources(2, 1, 1), 1),
    #     ('yellow', TaskResources(2, 2, 3), 1),
    # ]
    #
    # capacity = TaskResources(8, 5, 4)
    #
    # # bagged = knapsack01_dp(items, capacity, TaskResources)
    # bagged = knapsack01_dp(items, capacity)
    #
    # print bagged

    FognodeResources = [TaskResources(20, 20, 25), ["type_A"]]

    with open("../apps/webApplication.json") as f:
            app_dict = json.load(f)
            tasks = app_dict["IoTapplication"]["tasks"]

    taskgraph = DiGraph()
    for task in tasks:
        if not task['id'] in taskgraph:
            taskgraph.add_node(task["id"])
        data = str(task["DATA"])
        tr = TaskResources(ram=int(task['RAM']), cpu=int(
            task['CPU']), hdd=int(task['HDD']))
        taskgraph.node[task["id"]] = [tr, data]
        for dest in task["dest"]:
            taskgraph.add_edge(task["id"], dest["id"])

    print "random = ", strategy_random_resource(taskgraph, FognodeResources)
    print "max fanout = ", strategy_max_fanout(taskgraph, FognodeResources)
    print "components = ", strategy_strong_components(taskgraph, FognodeResources)
    print "knapsack", strategy_maximise_coverage_knapsack(taskgraph, FognodeResources)

    print ""

