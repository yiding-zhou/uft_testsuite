import core

priority = -100

def run():
    ## test 'listports'
    ports_info = core.ports_configured()
    resp = core.execute_rule("listports")
    resp = core.ports_from_resp(resp)
    if len(resp) != len(ports_info):
        return False

    pcis_in_serv = set([p[1] for p in resp])
    pcis_in_conf = set([p["pci"] for p in ports_info])

    if pcis_in_serv != pcis_in_conf:
        return False

    ## test 'flush' and 'list'
    for port_id, _ in enumerate(ports_info):
        cmd = "flow flush " + str(port_id)
        if core.error_from_resp(core.execute_rule(cmd)):
            return False

        cmd = "flow list " + str(port_id)
        resp = core.execute_rule(cmd)
        if len(core.rules_from_resp(resp)) != 0:
            return False

    return True
