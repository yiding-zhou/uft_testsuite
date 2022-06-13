import os
import core

cmd = "flow create %d ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end"

def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)
        resp1 = core.execute_rule(cmd % i)
        resp2 = core.execute_rule(cmd % i)
        if core.ruleno_from_resp(resp1) != 0 or core.ruleno_from_resp(resp2) != -1:
            print("resp1 = ", resp1)
            print("resp2 = ", resp2)
            return False

    return True
