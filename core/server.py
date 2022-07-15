import time
import os
import random
from threading import Thread
import yaml
from pexpect import pxssh, spawn, EOF, TIMEOUT
import rule

remote_dpdk_dir = "lib"

remote_uft_dir = "host_uft"
remote_uft_base = "UFT"
remote_run_log = "run_log"
conf_prefix = "server_conf"
conf_postfix = ".yaml"
conf_cert_postfix= ".with_cert"

def _build_uft_check(srv):
    find_cmd = "find %s/%s " % (srv.remote_testdir, remote_uft_dir)
    check_map = {
        "docker": {"cmd": "docker images|grep " + srv.image_prefix, "done": False},
        "qos": {"cmd": find_cmd + " -name qos_pb2.py", "done": False},
        "flow": {"cmd": find_cmd + " -name flow_pb2.py", "done": False},
        "cython": {"cmd": find_cmd + " -name *.so", "done": False}
    }
    done = True
    for _ in range(0, srv.build_check_count):
        time.sleep(srv.build_check_interval)
        for chk in check_map:
            if check_map[chk]["done"]:
                continue

            if len(srv._excute_cmd(check_map[chk]["cmd"])) != len(srv.versions):
                print("building %s ......" % chk)
                done = False
            else:
                check_map[chk]["done"] = True

        if done:
            break
        done = True

    if done:
        print("build done")
    else:
        print("build not done, timeout...")


class dut_context:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ssh_host = cfg.get("ssh").get("host")
        self.ssh_port = cfg.get("ssh").get("port", 22)
        self.ssh_user = cfg.get("ssh").get("user")
        self.ssh_passwd = cfg.get("ssh").get("passwd")

        self.grpc_auth = cfg.get("grpc").get("auth")
        self.grpc_host = cfg.get("grpc").get("host")
        self.grpc_port = 50051

        self.versions = cfg.get("versions")
        self.remote_testdir = cfg.get("remote_testdir", "/root/uft_testdir")
        self.current_version = -1
        self.docker = False
        self.image_prefix = cfg.get("image_prefix", "uft_test")
        self.pcis = cfg.get("pcis")

        self.build_check_count = 120
        self.build_check_interval = 60
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        dirs = self.cwd.split("/")
        self.local_uft_dir = "/".join(dirs[:-2])
        self.local_uft_name = dirs[-3]
        self.current_run_log = ""

    def _clean_uft(self, clean_files=False):
        print("=============== stop building docker images ===============")
        docker_cmd = "ps aux| grep docker| grep build| grep " + self.image_prefix
        docker_cmd += "| awk '{print $2}' | xargs kill 2>/dev/null"
        self._excute_cmd(docker_cmd)
        print("=============== stop running UFT in docker ===============")
        docker_cmd = "(which docker > /dev/null 2>&1) && "
        docker_cmd += "(docker ps | grep " + self.image_prefix
        docker_cmd += "| awk '{print $1}'|xargs docker stop 2>/dev/null)"
        self._excute_cmd(docker_cmd)

        print("=============== stop running UFT in host ===============")
        host_cmd = 'ps aux|grep "python3 " | grep "%s/%s"' % (
            self.remote_testdir, remote_uft_dir)
        host_cmd += " | awk '{print $2}' | xargs kill 2>/dev/null"
        self._excute_cmd(host_cmd)
        if clean_files:
            self._clean_uft_files()

        print("=============== DUT clean done==========================")

    def _clean_uft_files(self):
        print("=============== clean images of uft_test================")
        docker_cmd = "(which docker > /dev/null 2>&1) && "
        docker_cmd += "(docker images | grep " + self.image_prefix
        docker_cmd += "| awk '{print $3}'|xargs docker rmi -f 2>/dev/null)"
        self._excute_cmd(docker_cmd)
        print("=============== clean test dir==========================")
        self._excute_cmd("rm -rf " + self.remote_testdir)

    def _excute_cmd(self, cmd, timeout=30, echo=True):
        ssh = pxssh.pxssh(encoding="utf-8")
        ssh.login(self.ssh_host, self.ssh_user, self.ssh_passwd,
                  port=self.ssh_port, original_prompt="[$#>]")
        if echo:
            print(cmd)
        ssh.sendline(cmd)
        ssh.PROMPT = "#"
        ssh.prompt(timeout)
        output = ssh.before
        ssh.logout()
        output = output.rsplit("\r\n")
        result = []
        for o in output:
            if "[PEXPECT]" in o or o == cmd:
                continue
            result.append(o)

        for r in result:
            print(r)
        return result

    def _download(self, src, dst="."):
        command = "scp -r -v {0}@{1}:{2} {3}".format(
            self.ssh_user, self.ssh_host, src, dst)
        if self.ssh_port is not None and self.ssh_port != 22:
            command = "scp -r -v -P {0} -o NoHostAuthenticationForLocalhost=yes {1}@{2}:{3} {4}".format(
                str(self.ssh_port), self.ssh_user, self.ssh_host, src, dst
            )
        self._spawn_scp(command)

    def _upload(self, src, dst):
        command = "scp -r -v {0} {1}@{2}:{3}".format(
            src, self.ssh_user, self.ssh_host, dst)
        if self.ssh_port is not None and self.ssh_port != 22:
            command = "scp -r -v -P {0} -o NoHostAuthenticationForLocalhost=yes {1} {2}@{3}:{4}".format(
                str(self.ssh_port), src, self.ssh_user, self.ssh_host, dst
            )
        self._spawn_scp(command)

    def _spawn_scp(self, scp_cmd):
        p = spawn(scp_cmd)
        time.sleep(0.5)
        ssh_newkey = "Are you sure you want to continue connecting"
        i = p.expect([ssh_newkey, "[pP]assword", "# ", EOF, TIMEOUT], 120)
        if i == 0:  # add once in trust list
            p.sendline("yes")
            i = p.expect([ssh_newkey, "[pP]assword", EOF], 2)

        if i == 1:
            time.sleep(0.5)
            p.sendline(self.ssh_passwd)
            p.expect("Exit status 0", 60)

        if i == 4:
            print("SCP TIMEOUT error %d" % i)

        p.close()

    def _gen_build_sh(self):
        print("=============== generate build.sh & upload to DUT=============")
        sh = open(self.cwd + "/build.sh", "w+")
        sh.write("#/bin/bash\n\n")
        sh.write("set -v\n\n")
        sh.write("testdir=%s\n" % self.remote_testdir)
        sh.write("dpdk_lib_dir=%s\n" % remote_dpdk_dir)
        sh.write("uft_dir=%s\n" % remote_uft_dir)
        sh.write("uft_base=%s\n" % remote_uft_base)
        sh.write("run_log=%s\n" % remote_run_log)
        sh.write("dcf_name=%s\n\n" % self.image_prefix)
        sh.write("versions=(" + " ".join(self.versions) + ")\n")

        cmd_file = open(self.cwd + "/build.run")
        cmd = cmd_file.read()
        cmd_file.close()
        sh.write(cmd)
        sh.close()
        self._upload(self.cwd + "/build.sh", self.remote_testdir)
        os.unlink(self.cwd + "/build.sh")

    def _gen_uft_conf(self, ver, use_cert=False):
        global remote_dpdk_dir
        print("=============== generate server_conf for %s===============" % ver)
        filename = self.cwd + "/" + conf_prefix + "." + ver
        conf = {"server": {}, "ports_info": []}
        libpath = "%s/libdpdk-%s/%s" % (self.remote_testdir,
                                        ver, remote_dpdk_dir)
        conf["server"]["ld_lib"] = libpath
        if use_cert:
            s_key = self.grpc_auth.get("server_key", None)
            s_crt = self.grpc_auth.get("server_cert", None)
            c_crt = self.grpc_auth.get("client_cert", None)
            if s_key and s_crt and c_crt:
                self._download(c_crt, self.cwd + "/ca.crt")
                if not os.access(self.cwd + "/ca.crt", os.R_OK):
                    raise Exception("download client_cert file from server failed")

                conf["server"]["server_port"] = self.grpc_port
                conf["server"]["cert_key"] = s_key
                conf["server"]["cert_certificate"] = s_crt 
                filename += conf_cert_postfix
        
        f = open(filename, "w+")
        conf["ports_info"] = self.pcis
        yaml.dump(conf, f)
        f.close()
        self._upload(filename, self.remote_testdir)
        os.unlink(filename)

    def _build_uft(self):
        self._excute_cmd("mkdir -p " + self.remote_testdir)
        self._gen_build_sh()

        # generate server_conf.yaml & scp it to server
        for ver in self.versions:
            self._gen_uft_conf(ver)
            if self.grpc_auth:
                self._gen_uft_conf(ver, use_cert=True)

        self.cert_ver = random.randint(0, len(self.versions) - 1)
        print("=============== upload UFT to DUT ===============")
        
        self._upload(self.local_uft_dir, self.remote_testdir)
        self._excute_cmd("cd %s && mv %s %s 2>/dev/null" %
                         (self.remote_testdir, self.local_uft_name, remote_uft_base))
        self._excute_cmd("cd " + self.remote_testdir +
                         " && chmod +x build.sh && ./build.sh > build.log 2>&1 &")

        self.tid_check = Thread(target=_build_uft_check, args=(self,))
        self.tid_check.start()
        print("building in DUT ......")
        self.tid_check.join()

    def _restart_uft(self, ver, use_cert, docker, logfile):
        global remote_dpdk_dir
        if use_cert and docker:
            raise Exception("start uft with cert in docker is not supported")

        if ver is None:
            if self.current_version == -1:
                self.current_version = 0
            ver = self.versions[self.current_version]

        if ver not in self.versions:
            return False

        if logfile is None:
            if docker:
                logfile = "uft_in_docker.log"
            else:
                logfile = "uft_in_host.log"

        self._stop_uft()
        cmd = ""
        if docker:
            cmd += "docker run -v /dev/hugepages:/dev/hugepages "
            # use /lib/firmware instead of /usr/lib/firmware on alpine
            cmd += "-v /lib/firmware:/lib/firmware:rw "

            for i, pci in enumerate(self.pcis):
                cmd += "-e PCIDEVICE_INTEL_COM_INTEL_ENS801F%d=%s " % (
                    i, pci["pci"])

            cmd += "--net=host --cap-add IPC_LOCK --cap-add SYS_NICE "
            cmd += "--device /dev/vfio:/dev/vfio " + self.image_prefix + ":" + ver
        else:
            conf = self.remote_testdir + "/" + conf_prefix + "." + ver
            if use_cert:
                conf += conf_cert_postfix
            uft_dir = "%s/%s/%s" % (self.remote_testdir, remote_uft_dir, ver)
            cmd = "cd " + uft_dir
            cmd += " && cp -f %s %s%s " % (conf, conf_prefix, conf_postfix)
            cmd += " && export LD_LIBRARY_PATH="
            cmd += "%s/libdpdk-%s/%s" % (self.remote_testdir, ver, remote_dpdk_dir)
            cmd += " && python3 -u %s/server.py " % uft_dir

        logfile = "%s/%s/%s" % (self.remote_testdir, remote_run_log, logfile)
        cmd += " >> " + logfile + " 2>&1 &"
        print("=============== start UFT ==========================")
        self._excute_cmd(cmd)
        chk_cmd = 'tail -n 3 %s 2>/dev/null | grep "now in server cycle" -c' % logfile

        count = 10
        while count > 0:
            time.sleep(6)
            res = self._excute_cmd(chk_cmd)
            if len(res) > 0 and "0" != res[0]:
                break
            count -= 1

        if count == 0:
            print("start uft timeout ......")
            return False
        
        self.docker = docker
        self.current_version = self.versions.index(ver)
        self.current_run_log = logfile
        return True

    def _stop_uft_docker(self):
        print("=============== stop UFT in docker ===============")
        image = self.image_prefix + ":" + self.versions[self.current_version]
        cmd = '''docker ps | grep "%s" | awk '{print $1}' | xargs docker stop 2>/dev/null''' % image
        self._excute_cmd(cmd)

        count = 5
        while count > 0:
            time.sleep(3)
            res = self._excute_cmd("docker ps | grep %s -c" % image)
            if len(res) > 0 and "0" == res[0]:
                break
            count -= 1

        if count == 0:
            print("stop uft in docker timeout...")

        return count != 0

    def _stop_uft_host(self):
        print("=============== stop UFT in host ===============")
        cmd = 'ps aux | grep python3 | grep "server.py" | grep "%s/%s"' % (
            self.remote_testdir, remote_uft_dir)
        self._excute_cmd(cmd + " | awk '{print $2}' | xargs kill 2>/dev/null")

        count = 5
        while count > 0:
            time.sleep(3)
            res = self._excute_cmd(cmd + " -c")
            if len(res) > 0 and "0" == res[0].strip():
                break
            count -= 1
        if count == 0:
            print("stop uft in host timeout...")
        return count != 0

    def _stop_uft(self):
        if self.docker:
            return self._stop_uft_docker()
        else:
            return self._stop_uft_host()

    def _insert_log_tag(self, tag, n):
        if not n or not isinstance(n, int):
            n = 0
        prefix = "===="
        while n > 0:
            prefix = prefix + "===="
            n -= 1

        cmd = 'echo "%s%s" >> %s' % (prefix, tag, self.current_run_log)
        self._excute_cmd(cmd, echo=False)

def init_dut(cfg):
    global dut
    dut = dut_context(cfg)
    rebuild = cfg.get("rebuild", False)
    dut._clean_uft(rebuild == True)
    if rebuild == True:
        dut._build_uft()


def restart_uft(ver=None, use_cert=False, docker=False, logfile=None):
    if use_cert and not dut.grpc_auth:
        raise Exception("You must configure grpc[auth]")
    rule.reset_rule_context(dut.cfg, use_cert)
    return dut._restart_uft(ver, use_cert, docker, logfile)


def ports_configured():
    return dut.pcis


def stop_uft():
    return dut._stop_uft()

def insert_log_tag(tag, n=None):
    dut._insert_log_tag(tag, n)

def execute_rule(r):
    insert_log_tag(r, 1)
    return rule._execute_rule(r)

def execute_command(cmd):
    dut._excute_cmd(cmd)

dut = None

__all__ = ["init_dut", "restart_uft", "ports_configured", "stop_uft", "insert_log_tag",
"execute_rule", "execute_command"]
