import os
import core

disable_docker = True

cmd = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions vf id 1 / end"

def run():
    core.execute_rule("flow flush 0")
    step = 1
    core.insert_log_tag("Step 1: add a valid SWITCH rule", 1)
    step += 1
    resp1 = core.execute_rule(cmd)
    core.insert_log_tag("Step 2: check the rule created successfully at step 1", 1)
    step += 1
    core.insert_log_tag("Step 3: add the rule at step 1 repeatedly", 1)
    step += 1
    resp2 = core.execute_rule(cmd)
    core.insert_log_tag("Step 4: check the rule created failed at step 3", 1)
    if core.ruleno_from_resp(resp1) != 0 or core.ruleno_from_resp(resp2) != -1:
        print("resp1 = ", resp1)
        print("resp2 = ", resp2)
        return False

    return True
