import sys
sys.path.append('core')
sys.path.append('cases')
import config
import inspect
import os
import atexit
import core

cases = []
global_config = None
versions = None

allow_list = []

def handler_on_exit():
    core.stop_uft()

class test_case:
    def __init__(self, name, func, disable_docker=False, priority=0, need_restart=False):
        self.name = os.path.basename(name)
        self.func = func
        self.disable_docker = disable_docker
        self.priority = priority
        self.need_restart = need_restart
        self.result_host = {}
        self.result_docker = {}

def get_case(mod):
    # get all functions from module
    func_all = inspect.getmembers(mod, inspect.isfunction)

    cases = [c[1] for c in func_all if c[1].__code__.co_argcount == 1]
    if len(cases) != 1:
        print("please implement function 'run()' that take 0 param in %s" %
              mod.__file__)
        raise Exception("Implement function error in %s" % mod.__file__)

    disable_docker = hasattr(mod, "disable_docker")
    priority = 0
    if hasattr(mod, "priority"):
        prio = getattr(mod, "priority")
        if isinstance(prio, int):
            priority = prio

    need_restart = False
    if hasattr(mod, "need_restart"):
        restart = getattr(mod, "need_restart")
        if isinstance(restart, bool):
            need_restart = restart

    return test_case(mod.__file__[:-3],
                    cases[0],
                    disable_docker=disable_docker,
                    priority=priority,
                    need_restart=need_restart)


def load_cases():
    global cases
    for filename in os.listdir("cases"):
        if filename[0] in (".", "_") or not filename.endswith(".py"):
            continue

        if allow_list and filename[:-3] not in allow_list:
            continue
        try:
            mod = __import__(filename[:-3])
            cases.append(get_case(mod))
        except Exception as e:
            print(e)
    cases.sort(key=lambda x: x.priority)
    return cases


def run_cases_host(cases, ver):
    print("Run Test Cases on Host")
    for c in cases:
        print(ver, "Run Host Case : %s" % c.name)
        try:
            core.insert_log_tag("Test Case : " + c.name + " Start")
            c.result_host[ver] = c.func(ver)
            core.insert_log_tag("Test Case : " + c.name + " End")
            if c.need_restart:
                core.restart_uft()
        except Exception as e:
            print(e)
            c.result_host[ver] = False

        if not c.result_host[ver]:
            print(">>>case : %s failed in host" % c.name)
    print("Run Test Cases on Host Done")

def run_cases_docker(cases, ver):
    print("Run Test Cases on Docker")
    for c in cases:
        if not c.disable_docker:
            print(ver, "Run Docker Case : %s" % c.name)
            try:
                core.insert_log_tag("Test Case : " + c.name + " Start")
                c.result_docker[ver] = c.func(ver)
                core.insert_log_tag("Test Case : " + c.name + " End")
                if c.need_restart:
                    core.restart_uft()
            except Exception as e:
                print(e)
                c.result_docker[ver] = False

            if not c.result_docker[ver]:
                print(">>>case : %s failed in docker" % c.name)
        else:
            print(ver, "Case : %s disable on docke" % c.name)
            c.result_docker[ver] = "N/A"


def generate_report(cases):
    name_fmt = "{:%d}"
    col_fmt = "|{:%d}"

    col0_width = 0
    ver_width = 0
    for c in cases:
        if col0_width < len(c.name):
            col0_width = len(c.name)

    name_fmt = name_fmt % col0_width

    for ver in versions:
        if ver_width < len(ver):
            ver_width = len(ver)
    col_fmt = col_fmt % ver_width
    env_width = len(versions) * (1 + ver_width) - 1
    env_fmt = "|{:%d}" % env_width
    line_len = (1 + ver_width) * 2 * len(versions) + col0_width
    line_env = name_fmt.format("") + env_fmt.format("host")
    line_env += env_fmt.format("docker") + "\n"

    line_ver = name_fmt.format("name")

    for ver in versions:
        line_ver += col_fmt.format(ver)
    for ver in versions:
        line_ver += col_fmt.format(ver)

    line_sep = ""
    for _ in range(0, line_len):
        line_sep += "-"
    line_sep += "\n"

    report = line_sep + line_env + line_sep
    report += line_ver + "\n" + line_sep

    for c in cases:
        report += name_fmt.format(c.name)
        for ver in versions:
            try:
                if c.result_host[ver] == True:
                    report += col_fmt.format("pass")
                elif c.result_host[ver] == False:
                    report += col_fmt.format("fail")
            except Exception as e:
                report += col_fmt.format("N/A")
        for ver in versions:
            try:
                if c.result_docker[ver] == True:
                    report += col_fmt.format("pass")
                elif c.result_docker[ver] == False:
                    report += col_fmt.format("fail")
                else:
                    report += col_fmt.format("N/A")
            except Exception as e:
                report += col_fmt.format("N/A")
        report += "\n" + line_sep
    print("Test result:")
    print(report)

#def switch_version(ver):
#    os.system("cp -f rpc_files/" + ver + "/* .")
#    core.flow_reload_module()

def run_cases(cases):
    for ver in versions:
        print("one")
        core.set_env(ver=ver, docker=False)
        core.restart_uft()
        run_cases_host(cases, ver)
        try:
            core.set_env(ver=ver , docker=True)
            core.restart_uft()
            run_cases_docker(cases, ver)
        except Exception as e:
            print("run docker case : ", e)


if __name__ == "__main__":
    cfg = config.init_config()
    versions = cfg.get("versions", ["v21.08", "v21.11", "v22.03", "v22.07","v22.11"])
    allow_list = cfg.get("allow_list", [])
    if not isinstance(allow_list, list):
        allow_list = []

    versions.sort()
    cfg["versions"] = versions
    global_config = cfg
    print("will test the versions : ", versions)

    atexit.register(handler_on_exit)
    core.init_dut(cfg)
    print("init dut done")
    cases = load_cases()
    try:
        run_cases(cases)
    except Exception as e:
        print(e)
        print(e.__traceback__.tb_frame.f_globals["__file__"])
        print(e.__traceback__.tb_lineno)
    print("all tests Done")
    core.stop_uft()
    generate_report(cases)
