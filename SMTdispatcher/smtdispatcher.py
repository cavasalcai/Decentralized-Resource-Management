from pysmt.shortcuts import Symbol, And, Plus, Int, ExactlyOne, Equals, get_formula_size, LE, Or, Not
from pysmt.shortcuts import Solver
from pysmt.typing import INT
import random
import json

SOLVER_NAME = 'z3'


class SMTDispatcher(object):

    def __init__(self, node_list, node_offers, app_dict):
        self.node_list = node_list
        self.latency_dict = self.build_latency_dict(self.node_list)
        self.node_offers = node_offers
        self.app_dict = app_dict

    @staticmethod
    def build_latency_dict(nodes):
        latencies = {}
        len_nodes = len(nodes)
        for i in range(len_nodes):
            for j in range(i + 1, len_nodes):
                s = str(i) + "-" + str(j)
                if i == 0:
                    latencies[s] = random.choice(range(10, 16))
                else:
                    latencies[s] = random.choice(range(1, 10))
        return latencies

    def getLatency(self, tf, ts):
        # This method will return the latency between two nodes using the latency dictionary. Considers that the latency
        # between "tf" and "ts" is equal to the latency between "ts" and "tf"
        # PARAM: "tf" is the first node where a task is placed
        # PARAM: "ts" is the second node where a dependency of task on "tf" is placed
        # RETURN: the latency between the two selected nodes
        if tf == ts:
            latency = 0
        else:
            s = str(tf) + "-" + str(ts)
            if s in self.latency_dict:
                latency = self.latency_dict[s]
            else:
                s = str(ts) + "-" + str(tf)
                latency = self.latency_dict[s]
        return latency

    def build_formula(self):

        t_list = []
        l_facts = []
        domain = []
        latencies = []
        task_constraints = []

        offers = dict()

        # the SLA of our application
        SLA = int(self.app_dict["IoTapplication"]["SLA"])

        # find the dependencies between tasks
        depend_list, tasks, prob = self.find_dependencies(self.app_dict)

        # encodes the domain constraints in the SAT formula
        # checks on what nodes every two tasks are mapped and save their
        # latency
        ln = len(self.node_list)
        for i in range(ln):
            d = {}
            for j in range(i, ln):
                for t in depend_list:
                    if i == j:
                        d[str(t[0]) + "_" + str(t[1])] = And(Equals(self.task(t[0]), Int(i)),
                                                             Equals(self.task(t[1]), Int(j)))
                    else:
                        d[str(t[0]) + "_" + str(t[1])] = Or(And(Equals(self.task(t[0]), Int(i)),
                                                                Equals(self.task(t[1]), Int(j))),
                                                            And(Equals(self.task(t[0]), Int(j)),
                                                                Equals(self.task(t[1]), Int(i))))
                for k, v in d.items():
                    t_tasks = k.split("_")
                    domain.append(v.Implies(self.get_latency(t_tasks[0], t_tasks[1]).Equals(Int(self.getLatency(i, j)))))

        # find the offers for each individual task
        # RETURN: a dictionary containing as a key the tasks and the value a
        # list of nodes which sent a bid for that particular task
        for k in self.node_offers:
            ln = len(self.node_offers[k])
            for i in range(ln):
                aTask = self.node_offers[k][i]
                offerSize = len(aTask)
                for j in range(offerSize):
                    theTask = aTask[j]
                    if theTask in offers:
                        offers[str(theTask)].add(int(k))
                    else:
                        aSet = set()
                        offers[theTask] = aSet
                        aSet.add(int(k))
        # check if all tasks have received an offer, if not the tasks will receive an offer from cloud, i.e., node 0
        if len(offers) != len(tasks):
            for t in tasks:
                if str(t) in offers:
                    continue
                else:
                    aSet = set()
                    offers[str(t)] = aSet
                    aSet.add(0)

        """creates a list of constraints that ensure a solution found by SMT does not exceed the available resources
        of a node. It is dependent on the bids received from each participant"""
        for node, bid in self.node_offers.items():
            bid_len = len(bid)
            task_c = []
            tasks_pos = []
            task_r = []
            neg_dict = {}
            diff_dict = {}
            for t in range(bid_len):
                tasks_cst = set()
                tmp_list = set()
                diff_list = []
                for n in bid[t]:
                    diff_list.append(n)
                diff_dict[t] = diff_list
                if len(bid[t]) == 0:
                    continue
                else:
                    tasks_pos.append(Or(Equals(self.task(tn), Int(int(node))) for tn in bid[t]))
                    for j in range(bid_len):
                        if j == t:
                            continue
                        else:
                            for tsk in bid[j]:
                                tasks_cst.add(tsk)
                            common_elem = list(set(bid[t]) & set(bid[j]))
                            if len(common_elem) != 0:
                                tt = set(bid[j]) - set(bid[t])
                                for et in tt:
                                    tmp_list.add(et)
                                neg_dict[t] = list((tasks_cst - set(bid[t])))
                                for e in common_elem:
                                    if e in diff_dict[t]:
                                        diff_dict[t].remove(e)
                    temp_list = list((tasks_cst - set(bid[t])) - tmp_list)
                task_c.append(Or(Equals(self.task(tn), Int(int(node))) for tn in bid[t]).Implies(
                    Not(Or(Equals(self.task(temp_list[tn]), Int(int(node))) for tn in range(len(temp_list))))))
            for t in range(bid_len):
                if t in neg_dict and t in diff_dict:
                    if len(diff_dict[t]) > 0:
                        task_c.append(Or(Equals(self.task(tn), Int(int(node))) for tn in diff_dict[t]).Implies(
                            Not(Or(Equals(self.task(neg_dict[t][tn]), Int(int(node))) for tn in range(len(neg_dict[t]))))))
            task_r.append(Or(tasks_pos))
            task_r.append(And(task_c))

            task_constraints.append(And(task_r))

        # creates the encoding for the tasks facts, i.e., where a task can be mapped
        task_facts = And(ExactlyOne(Equals(self.task(t), Int(n))
                                    for n in offers[t]) for t in offers.keys())
        # encodes the facts related to the latency between nodes
        latency_domain = And(domain)  # encodes the domain
        # encode the latency constraint for our problem
        problem = Plus(p for p in prob)
        # ensure that the solution does not exceed the available resources of a participant
        tasks_const = And(task_constraints)

        # put everything together into one sat formula
        facts = And(task_facts, tasks_const)
        f1 = facts.And(latency_domain)
        formula = f1.And(LE(problem, Int(SLA)))

        return formula, tasks, prob, latencies, task_facts, tasks_const, latency_domain

    @staticmethod
    def find_latency(t1, t2):
        # A macro to create a SMT symbol for latency between two nodes
        # PARAM: t1 and t2 are the two tasks sharing a dependency
        # RETURN: a SMT Symbol
        return Symbol("%s-%s" % (t1, t2), INT)

    @staticmethod
    def get_latency(t1, t2):
        # A macro function to create a SMT symbol to save the latency between
        # two tasks
        return Symbol("%s_latency_%s" % (t1, t2), INT)

    @staticmethod
    def task(t1):
        # A macro method to create a SMT sympol of a single tasks
        return Symbol("%s" % t1, INT)

    def find_dependencies(self, app):
        # Find the dependencies between tasks
        # PARAM: a description of an IoT application
        # RETURN: a list of tasks and their dependencies
        dep_list = []
        tasks = []
        prob = []

        for t1 in app["IoTapplication"]["tasks"]:
            tasks.append(self.task(str(t1["id"])))
            for d in t1["dest"]:
                dep_list.append([str(t1["id"]), str(d["id"])])
                prob.append(self.get_latency(str(t1["id"]), str(d["id"])))
        return dep_list, tasks, prob

    @staticmethod
    def print_solution(formula, tasks, prob, latencies):
        # A context (with-statment) lets python take care of creating and
        # destroying the solver.
        solution = {}
        with Solver() as solver:
            solver.add_assertion(formula)
            if solver.solve():
                for t in tasks:
                    print("%s = %s" % (t, solver.get_value(t)))
                    solution[t] = solver.get_value(t)
                # for s in prob:
                #     print("%s = %s" % (s, solver.get_value(s)))
                # for st in latencies:
                #     print("%s = %s" % (st, solver.get_value(st)))
                return solution
            else:
                print("No solution found")

    @staticmethod
    def print_solution_to_file(filename, testNr, total_time, offers, no_edgenodes, formula, tasks, prob, latencies):

        f = open("results/" + filename, "a+")
        f.write("\r\n")
        f.write("Test nr %d \r\n" % testNr)
        f.write("Formula size %d \r\n" % get_formula_size(formula))
        f.write("Total time took:" + str(total_time) + " ms \r\n")
        f.write("Number of edgenodes: " + str(no_edgenodes) + "\r\n")
        f.write("Node offers:" + str(offers) + "\r\n")
        f.write("Solution: \r\n")
        # A context (with-statment) lets python take care of creating and
        # destroying the solver.
        solution = {}
        with Solver(name=SOLVER_NAME) as solver:
            solver.add_assertion(formula)
            if solver.solve():
                for t in tasks:
                    f.write("%s = %s \r\n" % (t, solver.get_value(t)))
                    solution[t] = solver.get_value(t)
                # for s in prob:
                #     f.write("%s = %s \r\n" % (s, solver.get_value(s)))
                # for st in latencies:
                #     f.write("%s = %s \r\n" % (st, solver.get_value(st)))
                return solution
            else:
                f.write("No solution found\r\n")
        f.close()


if __name__ == '__main__':
    # the offers received from the bidders
    node_offers = {"1": [["t1", "t2"], ["t3", "t4"]], "2": [["t3", "t4"], ["t1"], ["t6", "t7"]], "3": [["t4, t5"],
                                                                                                       ["t2", "t3", "t6"]], "4": [["t2", "t4", "t5"], ["t7"]]}

    # read the JSON file containing the application description
    with open("applicationDescription.json") as f:
        app_dict = json.load(f)

    # latency dictionary of all bidding nodes
    # latency_dict = {"1-2": 4, "1-3": 2, "1-4": 5, "2-3": 3, "2-4": 6, "3-4": 1}
    latency_dict = app_dict['IoTapplication']['latency_dict']
    node_list = [0,1, 2, 3, 4]

    formula, tasks, prob, latencies = build_formula(node_list, latency_dict, node_offers, app_dict)

    # print formula.serialize()
    # print get_formula_size(formula)
