#
#import core

#cmd_file = "cmd.dcf.succ"

#def run():
#    cmds = []

#    with open(cmd_file, "r") as f:
#        txt = f.read()
#        txt = txt.split("\n")
#        for cmd in txt:
#            cmd = cmd.strip()
#            if not cmd:
#                continue
#            cmds.append(cmd.replace("create", "validate"))

#    for cmd in cmds:
#        resp = core.execute_rule(cmd)
#        if core.error_from_resp(resp):
#            return False
#    return True
