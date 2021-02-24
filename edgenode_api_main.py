from flask_restful import Resource, Api
import os
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, Response
from werkzeug import secure_filename
import subprocess
from networkx import Graph, DiGraph
import random
from IPython import embed
import operator
from random import choice
from networkx.algorithms.components import *
from networkx.algorithms.traversal import *
import copy
from edgenode.taskresource import make_vector
from edgenode.bid_strategies import *
import socket
from functools import wraps

import sys


app = Flask(__name__)
api = Api(app)

TaskResources = make_vector('ram cpu hdd')
taskgraph = DiGraph()


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'jeffkoons' and password == 'likesweirdbaloons'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def build_taskgraph(tasks):
    """ graph from the task json with TaskResource named tuples living in nodes """
    global taskgraph
    for task in tasks:
        if not task['id'] in taskgraph:
            taskgraph.add_node(task["id"])
        data = str(task["DATA"])
        tr = TaskResources(ram=int(task['RAM']), cpu=int(
            task['CPU']), hdd=int(task['HDD']))
        taskgraph.node[task["id"]] = [tr, data]
        for dest in task["dest"]:
            taskgraph.add_edge(task["id"], dest["id"])

    return taskgraph


@app.route('/get_bid', methods=['GET'])
@requires_auth
def get_bid():
    print 'Calculating bids..',
    bids = {
        "strategy_max_fanout": strategy_max_fanout(taskgraph, EdgenodeResources),
        "strategy_strong_components": strategy_strong_components(taskgraph, EdgenodeResources),
        "strategy_random_resource": strategy_random_resource(taskgraph, EdgenodeResources),
       "strategy_maximise_coverage_knapsack": strategy_maximise_coverage_knapsack(taskgraph, EdgenodeResources)
    }
    print 'done.'
    print 'Bidding for..', bids
    return jsonify(bids)


@app.route('/tasks', methods=['POST'])
@requires_auth
def tasks_recv():
    """ receive and build taskgraph 
    {"tasks": [{"id": "t1", "RAM": "12", "HDD": "1",CPU": "15", "dest": [{"id": "t2"}]},... 
    """
    recv_json = request.get_json()
    build_taskgraph(recv_json)
    return 'ok'


@app.route('/set_resources', methods=['POST'])
@requires_auth
def set_resources():
    """ Set the edgenode's resources for debugging """
    global available_resources
    global EdgenodeResources
    recv_json = request.get_json()
    for resourcename, value in recv_json.items():
        available_resources[resourcename] = value
    # TODO make this better
    EdgenodeResources = [TaskResources(ram=int(available_resources['RAM']), cpu=int(
        available_resources['CPU']), hdd=int(available_resources['HDD'])), available_resources['DATA']]

    print 'Available resources set to', EdgenodeResources
    return 'Available resources set to ' + str(available_resources)


if __name__ == '__main__':
    """ if called with port argument, run on that port instead of default 5000 """

    try:
        port = int(sys.argv[1])
    except IndexError:
        port = 5000
    print "I am edgenode", socket.gethostname(), 'with address', get_ip()
    global available_resources
    global EdgenodeResources

    tasks = {
        "tasks": [
            {"id": "t1", "RAM": "12", "HDD": "1",
                "CPU": "15", "dest": [{"id": "t2"}]},
            {"id": "t2", "RAM": "32", "HDD": "1", "CPU": "15",
                "dest": [{"id": "t1"}, {"id": "t3"}, {"id": "t4"}]},
            {"id": "t3", "RAM": "32", "HDD": "2",
                "CPU": "15", "dest": [{"id": "t6"}]},
            {"id": "t4", "RAM": "32", "HDD": "1",
                "CPU": "15", "dest": [{"id": "t5"}]},
            {"id": "t5", "RAM": "32", "HDD": "3",
                "CPU": "15", "dest": [{"id": "t7"}]},
            {"id": "t6", "RAM": "12", "HDD": "1",
                "CPU": "15", "dest": [{"id": "t7"}]},
            {"id": "t7", "RAM": "90", "HDD": "1", "CPU": "15", "dest": []}
        ]
    }

    available_resources = {"RAM": 100, "HDD": 7, "CPU": 70}
    EdgenodeResources = TaskResources(ram=int(available_resources['RAM']), cpu=int(
        available_resources['CPU']), hdd=int(available_resources['HDD']))

    print 'Available resources set to', available_resources
    app.run(host='0.0.0.0', port=port)

    # embed()
