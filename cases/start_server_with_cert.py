import core

disable_docker=True
priority=100

def run():
	core.restart_uft(use_cert=True)
	resp = core.execute_rule("listports")
	return len(core.ports_from_resp(resp)) == len(core.ports_configured())
