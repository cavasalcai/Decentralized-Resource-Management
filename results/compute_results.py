

def compute_res():
    avg_total_time = []
    avg_smt_time = []
    avg_formula = []
    sol_not_found = 0
    solution = []
    crr_sol = []
    no_sol_tests = []
    tests = []
    fr = open("montageGraph_20"
              ".txt", "r")
    for line in fr:
        if line.startswith("Test nr"):
            tests.append(int(line.split(" ")[2]))
        if line.startswith("No solution"):
            sol_not_found += 1
            no_sol_tests.append(tests[-1])
        if line.startswith("Total time"):
            avg_total_time.append(int(line.split(":")[1].split(" ")[0]))
        if line.startswith("Formula size"):
            avg_formula.append(int(line.split(" ")[2]))
        if line.startswith("t"):
            crr_sol.append(int(line.split(" = ")[1].split(" ")[0]))
            if line.startswith("t24"):
                solution.append(crr_sol)
                crr_sol = []
    fr.close()
    sol_found = 100 - sol_not_found
    f = open("montageGraphSMT_20.txt", "r")
    for line in f:
        if line.startswith("SMT"):
            avg_smt_time.append(int(line.split(":")[1].split(" ")[0]))
    f.close()
    smt_time_no_sol = [avg_smt_time[t] for t in no_sol_tests]
    for p in no_sol_tests:
        tests.remove(p)
    smt_time_sol = [avg_smt_time[t] for t in tests]
    return avg_total_time, sol_found, sol_not_found, avg_formula, avg_smt_time, solution, no_sol_tests, smt_time_no_sol, smt_time_sol


fw = open("montageGraph_results.txt", "a+")

fw.write("No. of Edgenodes \t Avg. bidding time \t Avg. total SMT time \t Avg. SAT time \t Avg. UNSAT time \t"
         " Successful mappings \t Full mapping at the edge \t Avg. formula size\r\n")

time, sol, no_sol, formula, smt, solution, no_sol_pos, smt_no, sat = compute_res()

full_sol = 0
for s in solution:
    if 0 in s:
        continue
    else:
        full_sol += 1

if len(sat) == 0:
    sat_sol = 0
else:
    sat_sol = sum(sat) / len(sat)

if len(smt_no) == 0:
    unsat_sol = 0
else:
    unsat_sol = sum(smt_no)/len(smt_no)


fw.write("      20" + "               \t    " + str(sum(time)/len(time)) + "            \t " + str(sum(smt)/len(smt))
         + "               \t  " + str(sat_sol) + "               \t  " +
         "               \t  " + str(unsat_sol) + "               \t  " + str(sol) + "               \t         " + str(full_sol) + "\t" + str(sum(formula)/len(formula)) + "\r\n")

fw.close()

# print "avg_time = ", time
# print "sol = ", sol
# print "no_sol = ", no_sol
# print "avg_formula = ", sum(formula)/len(formula)
# print "avg_smt_time = ", smt
# print "solution = ", solution
# print no_sol_pos
# print "smt no = ", sum(smt_no)/len(smt_no)
# print "sat = ", sum(sat)/len(sat)