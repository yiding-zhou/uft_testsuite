import core

cmd0 = "flow create %d ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end"
cmd1 = "flow create %d ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end"
cmd2 = "flow create %d ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions vf id 3 / end"
cmd3 = "flow create %d ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end"


def run():
    for i, _ in enumerate(core.ports_configured()):
        core.execute_rule("flow flush %d" % i)
        core.execute_rule(cmd0 % i)
        core.execute_rule(cmd1 % i)
        core.execute_rule(cmd2 % i)
        core.execute_rule(cmd3 % i)
        core.execute_rule("flow flush %d" % i)
        resp = core.execute_rule(cmd2 % i)
        if core.ruleno_from_resp(resp) != 0:
            print("resp = ", resp)
            return False

    return True
