import requests
from requests.auth import HTTPBasicAuth
import json
from multiprocessing import Process, Pool
import time
from pysmt.shortcuts import get_formula_size
from random import choice, sample
from flask import Flask
from flask_restful import Resource, Api
from functools import partial
from pysmt.shortcuts import get_formula_size
import random
import urllib2
from IPython import embed
from SMTdispatcher.smtdispatcher import SMTDispatcher
from edgenode_api_main import requires_auth
import argparse

app = Flask(__name__)
api = Api(app)


def flatten(*args):
    """ generator that flattens nested structure to list of elements """
    for x in args:
        if hasattr(x, '__iter__'):
            for y in flatten(*x):
                ""
        else:
            yield x


def check_alive(edgenode):
    """ check if edgenode is alive """
    proto, host, port = edgenode.split(':')
    host = host.replace("//", "")
    port = int(port)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    if result == 0:
        return True
    return False


def millis():
    return int(round(time.time() * 1000))


def contact_edgenode(control_res, edgenode, verbose=False):
    start_time = millis()

    if not check_alive(edgenode):
        print "WARNING:", edgenode, "is not alive, aborting."
        return -1

    print edgenode, 'setting node resources',
    if control_res:
        data = choice([["type_A", "type_B", "type_C"], ["type_A", "type_B"], ["type_C", "type_A", "type_C"],
                       ["type_B", "type_C"]])
        ram = choice(range(25, 40))
        cpu = choice(range(25, 40))
        hdd = choice(range(25, 40))
        available_resources = {"RAM": ram, "HDD": hdd, "CPU": cpu, "DATA": [str(d) for d in data]}
        resp = requests.post(edgenode + "/set_resources",
                         json=available_resources, auth=credentials, timeout=20)
        print resp.status_code
        if verbose:
            print resp.text

    print edgenode, 'posting tasks',
    resp = requests.post(edgenode + "/tasks", json=tasks,
                         auth=credentials, timeout=20)
    print resp.status_code
    if verbose:
        print resp.text
        
    print edgenode, 'getting bids',
    resp = requests.get(edgenode + "/get_bid", auth=credentials, timeout=20)
    print resp.status_code
    if verbose:
        print resp.text
    # print 'WARNING we need to change this, now its all offers flattened'
    # this is the flattened out tasks that the node returned to us
    bidtasks = list([str(l) for l in t] for k,t in resp.json().items())

    return (bidtasks, millis() - start_time)


def parse_args():
    """
    Create the options and parse the arguments given as input by the user.
    :return: an argparse object.
    """

    parser = argparse.ArgumentParser(description="Find afeasible deployment strategy such that all "
                                                 "application's requirements are satisfied.")
    parser.add_argument('-a', '--application_file', type=str, help='Give the name of the application model file.',
                        required=True)
    parser.add_argument('-e', '--edge_nodes', type=str, help='Give the name of the file containing the list of '
                                                             'edge nodes.',
                        required=True)
    parser.add_argument('-r', '--results_file', type=str, help='Give the name of the file where results are saved. '
                                                                 'The default is: results_file.',
                        default='results_file')
    parser.add_argument('-s', '--stdout', action='store_true', help='Print the results on the python console.'
                                                                     'The default value is False.')

    parser.add_argument('-t', '--tests', type=int, help='Give the total number of tests.', default=1)

    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = parse_args()

    app_file = args.application_file
    edge_nodes_file = args.edge_nodes
    results_file = args.results_file
    print_flag = args.stdout
    no_tests = args.tests

    i = 0
    control_res = True
    with open("apps/" + app_file + ".json") as f:
        app_dict = json.load(f)
        tasks = app_dict["IoTapplication"]["tasks"]

    with open("edgeArchitecture/" + edge_nodes_file + ".json") as e_file:
        edge_nodes_dict = json.load(e_file)
        edge_nodes = [str(node['ip']) for node in edge_nodes_dict['edgeArchitecture']['nodes']]

    credentials = HTTPBasicAuth('jeffkoons', 'likesweirdbaloons')
    pool = Pool(processes=len(edge_nodes))
    while i != no_tests:
        start_time = millis()
        func = partial(contact_edgenode, control_res)
        results = pool.map(func, edge_nodes)
        control_res = False
        total_time = str(millis() - start_time)
        node_list = [idx + 1 for idx, edgenode in enumerate(edge_nodes)]
        node_list.append(0) # add the cloud node
        print "the deployment strategy is:"
        start_time = millis()
        node_offers = {str(idx + 1):[k for k in tup[0]] for idx,tup in enumerate(results) if tup != -1}
        problem_instance = SMTDispatcher(node_list, node_offers, app_dict)
        formula, task, prob, latencies, task_facts, tasks_const, latency_domain = problem_instance.build_formula()
        if print_flag:
            solution = SMTDispatcher.print_solution(formula, task, prob, latencies)
        else:
            solution = SMTDispatcher.print_solution_to_file(results_file + "_" + str(len(edge_nodes)) +".txt", i,
                        total_time, node_offers, len(edge_nodes), formula, task, prob, latencies)
            f = open("results/" + results_file + "_" + str(len(edge_nodes)) + ".txt", "a+")
            f.write("SMT took:" + str(millis() - start_time) + " ms \r\n")
            f.write("TaskFacts:" + str(get_formula_size(task_facts)) + "\r\n")
            f.write("TaskConst:" + str(get_formula_size(tasks_const)) + "\r\n")
            f.write("LatencyDomain:" + str(get_formula_size(latency_domain)) + "\r\n")
        print "i = ", i
        print "Finished."
        i += 1
        f.close()









