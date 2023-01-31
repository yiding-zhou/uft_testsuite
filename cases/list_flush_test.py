import core

priority = -100

def run(ver):
    ## test 'listports'
    ports_info = core.ports_configured(ver)
    resp = core.execute_rule("listports")
    resp = core.ports_from_resp(resp)
    if len(resp) != len(ports_info):
        return False

    pcis_in_serv = set([p[1] for p in resp])
    pcis_in_conf = set([p["pci"] for p in ports_info])

    if pcis_in_serv != pcis_in_conf:
        return False

    ## test 'flush' and 'list'

    cmd = "flow flush 0"
    if core.error_from_resp(core.execute_rule(cmd)):
        return False

    return True
