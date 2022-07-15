import os
import core

disable_docker = True

cmd = "flow create 0 ingress pattern eth / ipv4 / udp src spec 8017 src mask 65520 / end actions vf id 1 / end"

def run():
    core.execute_rule("flow flush 0")
    resp1 = core.execute_rule(cmd)
    resp2 = core.execute_rule(cmd)
    if core.ruleno_from_resp(resp1) != 0 or core.ruleno_from_resp(resp2) != -1:
        print("resp1 = ", resp1)
        print("resp2 = ", resp2)
        return False

    return True
