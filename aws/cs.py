#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

'''
The script automates to show and config devices via console
https://issues.amazon.com/issues/DXDEPLOY-525
'''


import paramiko
import os
import subprocess
import re
import time
from enum import Enum, unique
import logging
import argparse
from os.path import expanduser
import ipaddress


HOME = expanduser("~")
TIME_APPENDIX = time.strftime("-%Y%m%d-%H%M%S")
# LOG_FILE = '{}/console-log{}.log'.format(str(HOME),TIME_APPENDIX)

ROOT_PASSWORDs_OF_NEW_DEVICE = ["Juniper123", "",  "juniper123", "root123"]
ROOT_PASSWORD = "Juniper123"

def log_file_with_device(device):
    name = '{}/console-log-{}{}.log'.format(str(HOME), device, TIME_APPENDIX)
    return name


# OUTPUT_FILE = '{}/console-output{}.txt'.format(str(HOME),TIME_APPENDIX)


class FailConnectBastion(Exception):
    pass


class TooManyModeChange(Exception):
    pass

class FailConnectConsoleFromBastion(Exception):
    pass


class ConnecctionBroken(Exception):
    pass


class FailConnectRouter(Exception):
    pass


class WrongMethod(Exception):
    pass


class Fail_Enter_Router_Login(Exception):
    pass


class TooManyHistoryShow(Exception):
    pass


class ConsoleDBNonAccessible(Exception):
    pass


class WrongConsoleCredential(Exception):
    pass

class UnExpectedOutput(Exception):
    pass


@unique
class CSB_State(Enum):
    USERNAME_REQUIRED = "USERNAME_REQUIRED"
    PASSWORD_REQUIRED = "PASSWORD_REQUIRED"
    RETRY = "RETRY"
    WAIT_AFTER_SEND_USERNAME = "WAIT_AFTER_SEND_USERNAME"
    WAIT_AFTER_SEND_PASSWORD = "WAIT_AFTER_SEND_PASSWORD"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"
    NO_RESPONSE = "NO_RESPONSE"


@unique
class Response(Enum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"
    NO_RESPONSE = "NO_RESPONSE"
    UNKOWN = "UNKOWN"
    PIPE_BROKEN = "PIPE_BROKEN"
    YES_NO_CHECK = "YES_NO_CHECK"

@unique
class RouterUIState(Enum):
    SHELL = "SHELL"
    CLI = "CLI"
    CONFIG = "CONFIG"
    LOGIN = "LOGIN"
    PASSWORD = "PASSWORD"
    UNKOWN = "UNKOWN"
    TBD = "TBD"  # like --(more

DEFAULT_RESPONSE_MAP = {
    r"^$": Response.NO_RESPONSE,
    r"Broken pipe": Response.PIPE_BROKEN,
    r"Connection closed": Response.PIPE_BROKEN,
    r"Authentication failed": Response.FAILURE,

}

def make_sure_connection_right(response_type):
    if response_type is Response.PIPE_BROKEN:
        raise ConnecctionBroken

TELNET_CONSOLE_RESPONSE_MAP= {
    r"sername:$": Response.SUCCESS,
    r"sername: $": Response.SUCCESS,
    r"login:": Response.SUCCESS
}

SUCCESS_LOGIN_CONSOLE_RESPONSE_MAP = {
    r"login: ": Response.SUCCESS,
    r"@.*> $": Response.SUCCESS,
    r"@.*:.*# $": Response.SUCCESS,
    r"Last login:": Response.SUCCESS,
    r"root@:~ #": Response.SUCCESS,
    r"root#" :  Response.SUCCESS,
    r"root>": Response.SUCCESS,
    r"@.*:.*#": Response.SUCCESS,
    r"@.*:.*%": Response.SUCCESS,
    r"@.*# $": Response.SUCCESS,
    r"@.*#": Response.SUCCESS,
    r"---\(more" : Response.SUCCESS,
    r"Auto Image Upgrade:":  Response.SUCCESS,
}

ROUTER_UI_STATE_MAP = {
    r"@.*> $": RouterUIState.CLI,
    r"@.*>": RouterUIState.CLI,
    r"root>":  RouterUIState.CLI,
    r"@.*:.*#": RouterUIState.SHELL,
    r"@.*:.*%": RouterUIState.SHELL,
    r"root.*:.*%": RouterUIState.SHELL,
    r"root.*:.*#": RouterUIState.SHELL,
    r"root#": RouterUIState.CONFIG,
    r"@.*\d+#": RouterUIState.CONFIG,
    r"login: $": RouterUIState.LOGIN,
    r"assword:$": RouterUIState.PASSWORD,
    r"---\(more": RouterUIState.TBD,
}

READ_BUFFER = 9999

class Credential:
    def __init__(self, username=None, password=None, ordin=None):
        self.username = username
        self.password = password
        self.ordin = ordin
    def get_password_from_odin(self):
        pass

class ConsoleBastion(object):

    def __init__(self, console_bastion):
        self.console_bastion = console_bastion

        self.same_state_number = 0
        self._state = "INIT"
        # self.channel = self._cb.channel

        self._ssh = get_paramiko_connection(device_name=self.console_bastion)
        if not self._ssh:
            logging.error("Failed to connect {}".format(self.console_bastion))
            raise FailConnectBastion
        self._channel = self._ssh.invoke_shell()
        self._state = "CONNECTED"

    def read_response(self):
        response = self.read()
        type = get_response_type(response)
        make_sure_connection_right(type)
        return response


    def send_command(self, cmd, hide = False):
        self.writeline(cmd, hide)


    def close(self):
        self._channel.close()
        self._ssh.close()


    def read(self):
        """ read a single line """
        sleep_second = 5            #after login router, it takes time for response.
        time.sleep(sleep_second)
        rxb = "".encode()
        while True:
            data = self._channel.recv(READ_BUFFER)
            if data is None or len(data) <= 0:
                break
            else:
                rxb += data
            break
        result = rxb.decode()
        logging.debug("Received:\n"+result)
        return result


    def writeline(self,cli, hide):
        cmd = cli+"\n"
        if not hide:
            logging.debug("Sent: " + cli)
        else:
            if len(cli) == 0:
                hide_message = ""
            else:
                hide_message = cli[0]+"*"*max(0,len(cli)-1)
            logging.debug("Sent: {}".format(hide_message))
        self._channel.send(cmd.encode())


class ConsoleHost:
    def __init__(self, console_bastion, host, port, method = "telnet"):
        self.console_bastion = console_bastion
        self.host = host
        self.port = str(port)
        self.method = method
        self.credential = None
        self.connected = False
        self.response_after_last_login_try = ""
        cli = ""
        if self.method == "telnet":
            cli = " ".join([self.method, self.host, self.port])
        elif self.method == "ssh":
            raise WrongMethod("only support 'telnet', current method is {}".format(self.method))
        else:
            raise WrongMethod("only support 'telnet' or 'ssh', current method is {}".format(self.method))

        telnet_cs = Command(cli_to_device=cli, response_map=TELNET_CONSOLE_RESPONSE_MAP)
        telnet_cs.run_on_deivce(self.console_bastion)
        if telnet_cs.response_type is not Response.SUCCESS:
            raise FailConnectConsoleFromBastion("bastion response: \n{}".format(telnet_cs.response))


    def read_response(self):
        self.response = self.console_bastion.read_response()
        return self.response


    def send_command(self, cmd, hide = False):
        self.console_bastion.send_command(cmd, hide)


    def load_credential(self, credential):
        self.credential = credential


    def login_with_credential(self, credential):
        username = credential.username
        password = credential.password
        success, response = login_console(device=self.console_bastion, username=username, password=password)
        self.connected = success
        self.response_after_last_login_try = response
        return success



CLI_MODE_MAP = {
    r"@.*> $": Response.SUCCESS,
    r"@.*>$": Response.SUCCESS,
    r"@.*>": Response.SUCCESS,
    r"root>": Response.SUCCESS,
    r"\[yes,no\]": Response.YES_NO_CHECK,
}
CONFIG_MODE_MAP = {
    r"@.*# $": Response.SUCCESS,
    r"@.*#$": Response.SUCCESS,
    r"@.*#": Response.SUCCESS,
}
SHELL_MODE_MAP = {
    r"@.*:.*# $": Response.SUCCESS,
    r"@.*:.*#$": Response.SUCCESS,
    r"@.*:.*#": Response.SUCCESS,
    r"@.*:.*%": Response.SUCCESS,
}
class Router:
    def __init__(self, console, force_check_root_credential=False, is_new_device = False):
        self.console = console
        self.force_check_root_credential = force_check_root_credential
        self.is_new_device = is_new_device
        logging.debug("self.validate_router_credential = {}".format(self.force_check_root_credential))
        self.connected = False
        self.mode_change_count = 100 # against loop
        response = console.response_after_last_login_try
        self.response = response
        self.ui_mode = get_router_ui_type(response=response)
        self.is_right_default_root_password = False

        # check if we see "---(more"
        if self.ui_mode is RouterUIState.TBD:
            count = 20
            still_see_more = Response.SUCCESS # still see "--(more"
            #last_reponse = "" # save the last reponse to check the ui type
            while still_see_more is Response.SUCCESS and count>0:
                check_more_map = {
                    r"---\(more": Response.SUCCESS
                }
                space_command = Command(cli_to_device=" ", response_map=check_more_map)
                space_command.run_on_deivce(self)
                still_see_more = space_command.response_type
                response = space_command.response

            if count<1:
                raise TooManyHistoryShow

            self.response = response
            self.ui_mode = get_router_ui_type(response=response)

        if self.ui_mode is RouterUIState.SHELL or \
            self.ui_mode is RouterUIState.CLI or \
            self.ui_mode is RouterUIState.CONFIG:
            self.connected = True

        self.name = get_router_name(self.response)
        # print("Success connect to {}".format(self.name))

    def _login_router(self, username, password):
        device = self
        username_response_map = {
            "^$": Response.NO_RESPONSE,
            "assword: $": Response.SUCCESS,
            "assword:$": Response.SUCCESS,
            r"Last login:": Response.SUCCESS,
            "@.*%": Response.SUCCESS,
            "@.*#": Response.SUCCESS,
            "@.*>": Response.SUCCESS,
        }
        username_input = Command(cli_to_device=username, response_map=username_response_map)

        password_response_map = {
            r"^$": Response.NO_RESPONSE,
            r"login: $": Response.FAILURE,
            r"Login incorrect": Response.FAILURE,
            r"@.*> $": Response.SUCCESS,
            r"@.*:.*# $": Response.SUCCESS,
            r"@.*:.*#": Response.SUCCESS,
            r"@.*# $": Response.SUCCESS,
            r"@.*#": Response.SUCCESS,
            r"@.*:.*%": Response.SUCCESS,
            r"Last login:": Response.SUCCESS,
            r"root": Response.SUCCESS,
            r"Auto Image Upgrade": Response.SUCCESS,
        }
        password_input = Command(cli_to_device=password, response_map=password_response_map)

        username_input.run_on_deivce(device)
        if username_input.response_type is not Response.SUCCESS:
            logging.error("username response not success @_login_router")
            return False, username_input.response

        password_input.run_on_deivce(device, hide=True)
        if password_input.response_type is Response.SUCCESS:
            self.ui_mode = get_router_ui_type(response=password_input.response)
            self.connected = True
            logging.info("Success login router with mode {}".format(self.ui_mode))
            return True, password_input.response

        else:
            logging.info("Fail to login device ")
            return False, password_input.response
        

    def login_with_credential(self, credential):
        username = credential.username
        password = credential.password
        if self.ui_mode is RouterUIState.PASSWORD or \
            self.ui_mode is RouterUIState.UNKOWN:
            if not self._get_start_with_login():
                raise Fail_Enter_Router_Login("ui_mod: {}".format(self.ui_mode))

        if not self.is_new_device:
            success, response = self._login_router(username=username, password=password)
        else:
            success, response = self._login_router_try(username=username, password=password)
        self.connected = success
        self.response_after_last_login_try = response

        return success

    def _login_router_try(self, username, password):
        success = False
        response = ""
        # print("root password: {}".format(password))
        if password is not None:
            success, response = self._login_router(username=username, password=password)
        if success:
            return success, response
        for pwd in ROOT_PASSWORDs_OF_NEW_DEVICE:
            success, response = self._login_router(username=username, password=pwd)
            if success:
                if pwd == ROOT_PASSWORD:
                    self.is_right_default_root_password = True
                return success, response
        return False, response

    def logout(self):
        logout_response_map = {
            r"login:": Response.SUCCESS,
            r"@.*> $": Response.FAILURE,
            r"@.*:.*# $": Response.FAILURE,
            r"@.*# $": Response.FAILURE,
        }
        retry = 100
        while retry>0:
            retry -= 1
            exit_command = Command(cli_to_device="exit",response_map=logout_response_map)
            exit_command.run_on_deivce(self)
            if exit_command.response_type is Response.SUCCESS:
                self.ui_mode = RouterUIState.LOGIN
                self.connected = False
                return True
        return False

    def _get_start_with_login(self):

        if self.ui_mode is RouterUIState.LOGIN:
            return True
        if self.connected:
            if self.force_check_root_credential:
                print("Logging out Router ")
                self.logout()
            else:
                logging.message("The current mode is {}".format(self.ui_mode))
                return True
        login_response_map = {
            r"login:": Response.SUCCESS,
        }
        retry = 5
        while retry<5:
            retry -= 1
            empty_command = Command(cli_to_device="",response_map=login_response_map)
            empty_command.run_on_deivce(self)
            if empty_command.response_type is Response.SUCCESS:
                self.ui_mode=RouterUIState.LOGIN
                return True
        return False


    def read_response(self):
        self.response = self.console.read_response()
        return self.response


    def send_command(self, cmd, hide = False):
        self.console.send_command(cmd, hide)

    def set_mode_to_cli(self):
        self.mode_change_count -= 1
        if self.mode_change_count < 0 :
            raise TooManyModeChange
            return False
        if not self.connected:
            raise FailConnectRouter("Cannot change mode before connected to router")
            return False
        if self.ui_mode is RouterUIState.SHELL:
            cli_cmd = Command(cli_to_device="cli",response_map=CLI_MODE_MAP)
            cli_cmd.run_on_deivce(self)
            if cli_cmd.response_type is not Response.SUCCESS:
                self.set_mode_to_cli()
            self.ui_mode = RouterUIState.CLI
        if self.ui_mode is RouterUIState.CONFIG:
            cli_cmd = Command(cli_to_device="exit",response_map=CLI_MODE_MAP)
            cli_cmd.run_on_deivce(self)
            if cli_cmd.response_type is Response.YES_NO_CHECK:
                cli_cmd = Command(cli_to_device="yes", response_map=CLI_MODE_MAP)
                cli_cmd.run_on_deivce(self)
            # if cli_cmd.response_type is not Response.SUCCESS:
            #    self.set_mode_to_cli()
            self.ui_mode = RouterUIState.CLI
        logging.info("Changed mode to cli")
        return True


    def set_mode_to_config(self):
        self.mode_change_count -= 1
        if self.mode_change_count < 0 :
            raise TooManyModeChange
            return False
        if not self.connected:
            raise FailConnectRouter("Cannot change mode before connected to router")
            return False
        if self.ui_mode is RouterUIState.SHELL:
            self.set_mode_to_cli()
        if self.ui_mode is RouterUIState.CLI:
            cli_cmd = Command(cli_to_device="config",response_map=CONFIG_MODE_MAP)
            cli_cmd.run_on_deivce(self)
            if cli_cmd.response_type is not Response.SUCCESS:
                self.set_mode_to_cli()
            self.ui_mode = RouterUIState.CONFIG
        logging.info("Changed mode to Config")
        return True


    def set_mode_to_shell(self):
        self.mode_change_count -= 1
        if self.mode_change_count < 0 :
            raise TooManyModeChange
            return False
        if not self.connected:
            raise FailConnectRouter("Cannot change mode before connected to router")
            return False
        if self.ui_mode is RouterUIState.CONFIG:
            self.set_mode_to_cli()
        if self.ui_mode is RouterUIState.CLI:
            cli_cmd = Command(cli_to_device="exit",response_map=SHELL_MODE_MAP)
            cli_cmd.run_on_deivce(self)
            if cli_cmd.response_type is not Response.SUCCESS:
                self.set_mode_to_cli()
            self.ui_mode = RouterUIState.SHELL
        logging.info("Changed mode to shell")
        return True

    def show_commands(self, clis):
        self.set_mode_to_cli()
        for cli in clis:
            self.show_command(cli)

    def shell_commands(self, clis):
        self.set_mode_to_shell()
        for cli in clis:
            self.shell_command(cli)

    def check_interface_iface(self, intf):
        cli = "show interfaces terse " + intf
        self.set_mode_to_cli()
        response = self.show_command(cli)
        def get_ip_from_response(response):
            r = r"\d+.\d+.\d+.\d+\/\d+"
            for word in response.split():
                if re.search(r,word):
                    return word.strip()
            return ""
        iface_str = get_ip_from_response(response)
        return iface_str


    def set_default_route_from_interface(self, intf, gw_seq = 1):

        iface_str = self.check_interface_iface(intf)
        iface = ipaddress.ip_interface(iface_str)
        network = iface.network
        gw_ip = str(network[gw_seq])
        cli = "set routing-options static route 0.0.0.0/0 next-hop {} no-readvertise".format(gw_ip)
        self.set_mode_to_config()
        self.write_config(cli)
        self.commmit_change()
        self.set_mode_to_cli()


    def show_command(self, cli):
        cli_cmd = Command(cli_to_device=cli, response_map=CLI_MODE_MAP)
        cli_cmd.run_on_deivce(self)
        response_type = cli_cmd.response_type
        retry_count = 10
        while response_type is Response.UNKOWN and retry_count > 0:
            enter_cmd =  Command(cli_to_device=" ", response_map=CLI_MODE_MAP)
            enter_cmd.run_on_deivce(self)
            response_type = enter_cmd.response_type
            retry_count -= 1
        print(self.response)
        return self.response

    def shell_command(self, cli):
        cli_cmd = Command(cli_to_device=cli, response_map=SHELL_MODE_MAP)
        cli_cmd.run_on_deivce(self)
        response_type = cli_cmd.response_type
        retry_count = 10
        while response_type is Response.UNKOWN and retry_count > 0:
            enter_cmd = Command(cli_to_device=" ", response_map=CLI_MODE_MAP)
            enter_cmd.run_on_deivce(self)
            response_type = enter_cmd.response_type
            retry_count -= 1
        return

    def write_configs(self, clis):
        if not self.is_new_device:
            return
        self.set_mode_to_config()
        for cli in clis:
            self.write_config(cli)

        self.show_compare()
        self.commmit_change()
        self.set_mode_to_cli()
        pass

    def write_config(self, cli):
        write_response_map = {
            r"@.*# $": Response.SUCCESS,
            r"@.*#$": Response.SUCCESS,
            r"@.*#": Response.SUCCESS,
        }
        print("cli: {}".format(cli))
        config_cmd = Command(cli_to_device=cli, response_map=write_response_map)
        config_cmd.run_on_deivce(self)

        if config_cmd.response_type is Response.SUCCESS:
            return True
        return False


    def commmit_change(self):
        commit_response_map = {
            r"commit complete": Response.SUCCESS,
            r"@.*# $": Response.SUCCESS,
            r"@.*#$": Response.SUCCESS,
            r"@.*#": Response.SUCCESS,
        }
        commit_cmd = Command(cli_to_device="commit", response_map=commit_response_map)
        commit_cmd.run_on_deivce(self)

        if commit_cmd.response_type is Response.SUCCESS:
            return True
        return False

    def show_compare(self):
        show_compare_response_map = {
            r"@.*# $": Response.SUCCESS,
            r"@.*#$": Response.SUCCESS,
            r"@.*#": Response.SUCCESS,
        }
        show_compare_cmd = Command(cli_to_device="show | compare | no-more", response_map=show_compare_response_map)
        show_compare_cmd.run_on_deivce(self)

        if show_compare_cmd.response_type is Response.SUCCESS:
            return True
        return False


    def set_router_name(self, router_name):
        cli = "set system host-name {}".format(router_name)
        self.set_mode_to_config()
        self.write_config(cli)
        self.show_compare()
        self.commmit_change()
        self.set_mode_to_cli()

    def set_root_password(self):
        self.set_mode_to_config()
        write_response_map = {
            r"New password:": Response.SUCCESS,
        }
        config_cmd = Command(cli_to_device="set system root-authentication plain-text-password", response_map=write_response_map)
        config_cmd.run_on_deivce(self)
        if config_cmd.response_type is not Response.SUCCESS:
            raise UnExpectedOutput("Set root password, router return is unexpected")

        password_response_map = {
            r"Retype new password:": Response.SUCCESS,
        }
        password_cmd = Command(cli_to_device=ROOT_PASSWORD, response_map=password_response_map)
        password_cmd.run_on_deivce(self)
        if password_cmd.response_type is not Response.SUCCESS:
            raise UnExpectedOutput("Input root password in setting root password, router return is unexpected")

        retry_password_response_map = {
            r"@.*# $": Response.SUCCESS,
            r"@.*#$": Response.SUCCESS,
            r"@.*#": Response.SUCCESS,
            r"root#": Response.SUCCESS,
        }
        retry_password_cmd = Command(cli_to_device=ROOT_PASSWORD, response_map=retry_password_response_map)
        retry_password_cmd.run_on_deivce(self)
        if retry_password_cmd.response_type is not Response.SUCCESS:
            raise UnExpectedOutput("Input root password in setting root password, router return is unexpected")
        self.commmit_change()
        return True


def get_paramiko_connection(device_name='consoles.bjs12'):
    if len(device_name) < 5:  #simple check if right device name
        return False

    client = paramiko.SSHClient()
    client._policy = paramiko.WarningPolicy()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("~/.ssh/config")
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            ssh_config.parse(f)

    user_config = ssh_config.lookup(device_name)

    cfg = {'hostname': device_name}
    if 'proxycommand' in user_config:
        rp = subprocess.check_output([os.environ['SHELL'], '-c', 'echo %s' % user_config['proxycommand']]).strip()
        rp_s = rp.decode("utf-8")

        cfg['sock'] = paramiko.ProxyCommand(rp_s)
    try:
        client.connect(**cfg)
        print("Connecting to %s \n" % device_name)
        return client
    except:
        print("Could not connect to {}".format(device_name))
        return False

class RouterConnectionBrokenException(Exception):
    # when router login out
    pass

# class ConsoleBrokenException(RouterConnectionBrokenException): ?
class ConsoleBrokenException(Exception):
    pass

def myprint(msg):
    print(msg)

def set_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,  # CRITICAL, ERROR,  #WARNING, INFO #DEBUG,
        format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s"
    )
    return


class Command:
    def __init__(self, cli_to_device, response_map,
                 default_response_map=DEFAULT_RESPONSE_MAP,
                 wait_response_time=1,
                 strategy=None,
                 retry=3):
        """

        :param cli_to_device:
        :param wait_response_time:
        :param response_map: {r'password:': "SUCCESS"}
        """
        #self._device = device
        self._cli = cli_to_device
        self._wait_time = wait_response_time
        self._response_map = response_map

        self._response_map.update(default_response_map)
        #print(self._response_map)

        self._strategy = strategy
        self._response = ""
        self._retry = retry
        self._regex_match = dict()
        self._last_device = None

    @property
    def response(self):
        return self._response

    def run_on_deivce(self, device, hide = False):
        self._last_device = device
        device.send_command(self._cli, hide)
        self.response_type = Response.NO_RESPONSE
        while self.response_type is Response.NO_RESPONSE and self._retry > 1:
            self._retry -= 1
            time.sleep(self._wait_time)
            self._response = device.read_response()
            self.response_type = self._check_resonse_type()

    def check_after_wait(self, second):
        time.sleep(second)
        self._response = self._last_device.read_response()
        self.response_type = self._check_resonse_type()
    def _check_resonse_type(self):
        type = get_response_type(response=self._response,
                                 response_map=self._response_map)
        return type


def get_response_type(response, response_map=DEFAULT_RESPONSE_MAP):
    result = dict()
    for reg, response_type in response_map.items():
        if re.search(reg, response):
            result[response_type] = response
    # priority: NO_RESPONSE > PIPE_BROKEN > FAILURE > SUCCESS > UNKNOWN
    if Response.NO_RESPONSE in result:
        return Response.NO_RESPONSE
    if Response.PIPE_BROKEN in result:
        return Response.PIPE_BROKEN
    if Response.FAILURE in result:
        return Response.FAILURE
    if Response.SUCCESS in result:
        return Response.SUCCESS

    return Response.UNKOWN


def get_router_ui_type(response, state_map = ROUTER_UI_STATE_MAP):
    #result = dict()
    for reg, state in state_map.items():
        if re.search(reg, response):
            return state
    return  RouterUIState.UNKOWN



#DEBUG_MODE = True
def login_console(device, username, password,
                  test_username_response=None, test_password_response=None, test_enter_response=None):
    username_response_map = {
        "^$": Response.NO_RESPONSE,
        "assword": Response.SUCCESS,
    }
    username_input = Command(cli_to_device=username, response_map=username_response_map)

    password_response_map = {
        r"^$": Response.NO_RESPONSE,
        r"name:$": Response.FAILURE,
        r"Authentication failed": Response.FAILURE,
    }
    password_input = Command(cli_to_device=password, response_map=password_response_map, retry=1)

    enter_input = Command(cli_to_device="", response_map=SUCCESS_LOGIN_CONSOLE_RESPONSE_MAP)
    if test_username_response is not None:
        device.set_response(test_username_response)
    username_input.run_on_deivce(device)

    if username_input.response_type is not Response.SUCCESS:
        logging.error("username response not success")
        return False, username_input.response

    if test_password_response is not None:
        device.set_response(test_password_response)
    password_input.run_on_deivce(device, hide=True)
    if password_input.response_type is not Response.NO_RESPONSE:
        if password_input.response_type is Response.FAILURE:
            pass
        else:
            pass


    if test_enter_response is not None:
        device.set_response(test_enter_response)
    enter_input.run_on_deivce(device)
    if enter_input.response_type is Response.SUCCESS:
        logging.info("Success login device ")
        return True, enter_input.response
    else:
        logging.info("Fail to login device ")
        return False, enter_input.response

def query_with_commnd(command):
    logging.info("starting query \"{}\"".format(command))
    p = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate()
    logging.info("complete query \"{}\"".format(command))
    #logging.debug("stdout is {}".format(stdout.decode()))
    #logging.debug("stderr is {}".format(stderr.decode()))

    if stdout:
        return stdout.decode()
    else:
        return stderr.decode()


def run_cli_remote(remote, command):
    cmd = "ssh -Aqt {remote} '{command}'".format(remote = remote, command = command)
    return query_with_commnd(cmd)


REGIONS = ['arn', 'bah', 'bjs', 'bom', 'cdg', 'cmh', 'cpt', 'dub', 'fra', 'gru', 'hkg', 'iad', 'icn', 'kix', 'lhr', 'nrt', 'osu', 'pdx', 'sfo', 'sin', 'syd', 'yul', 'zhy']
def get_regions_list():
    return REGIONS
class Password:
    console_cli = "/apollo/env/NetworkPasswordRetrievalTool/bin/getpassword --cred=neteng --fabric=prod --cred-type=console --region={reg}"
    console_username = "neteng"
    router_cli = "/apollo/env/envImprovement/bin/odin-get com.amazon.networking.managed.vpc-{reg}.local-user.root"
    router_username = "root"

    def __init__(self, root_password=None):
        self.regions = get_regions_list()
        self.passwords_of_region = dict()
        self.root_password = root_password
        #for reg in self.regions:
        #    self._query_password_of_region(reg)

    def get_password_in_region(self,reg):
        self.console_password = self.get_password(reg, self.console_cli)
        if self.root_password is None:
            self.router_password = "Juniper123"
        if self.root_password == "odin":
            self.router_password = self.get_password(reg, self.router_cli)
        #else:
        #    self.router_password = root_password
        #pass

    def get_password(self, reg, cli_template):
        cli = cli_template.format(reg=reg)
        remote = "nebastion-{reg}".format(reg=reg)
        response = run_cli_remote(remote, cli)
        password = self._get_password_from_response(response)
        return password

    def _get_password_from_response(self, response):
        words = response.split()
        if len(words) < 1:
            return ""
        '''
        MaterialName/Serial: com.amazon.networking.managed.prod-bom.console.local-user.neteng/6
        Principal: neteng
        Credential:  xxxxxxx 
        '''
        return words[-1]

def check_router_name(name, refer_name, force_same_name = False):
    '''
    make sure it does not login other product router
    if the name is the same as refer_name: return True
    if the name is other product device name: return False
    if name is not product device name, and force_same_name is False, return True

    :param name:
    :param refer_name:
    :param force_same_name: when it is True, return True only when name exactly same as refer_name
    :return:
    '''
    if name == refer_name:
        return True
    if force_same_name:
        return False
    p = r".*-.*-.*-r\d+"
    if re.search(p, name):
        return False
    return True

def get_router_name(response):
    p = r"@.*-.*-.*-r\d+"
    name = "noname"
    if re.search(p, response):
        name = re.findall(p, response)[0][1:]
    return name

def _initiate_subprocess(device):
    CORP_BASTION = "nebastioncorp-pdx"
    FETCH_CONSOLE_COMMAND = "ssh -tqA {1} /apollo/env/NRETools/bin/console.py -d {0} | grep {0}"
    return subprocess.Popen(
            FETCH_CONSOLE_COMMAND.format(device, CORP_BASTION),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def get_device_console_info(device):
    p = _initiate_subprocess(device)
    stdout, stderr = p.communicate()
    if stdout:
        str_stdout = stdout.decode()
        device_console_info = str_stdout.split()
        return {
            'device': device_console_info[0],
            'data_store': device_console_info[1],
            'bastion': device_console_info[2],
            'console': device_console_info[3],
            'port': device_console_info[4],
        }


class Login_Console:
    def __init__(self, device, region, bastion, console, port, root_password, force_check_root_credential=False, is_new_device=False):
        self.device = device
        self.region = region
        self.bastion = bastion
        self.console = console
        self.port = port
        self._update_credential(root_password)
        self.force_check_root_credential = force_check_root_credential
        self.is_new_device = is_new_device

    def _update_credential(self, root_password):
        a = Password(root_password=root_password)
        a.get_password_in_region(self.region)
        self.console_username = "neteng"
        self.console_password = a.console_password
        self.router_username = "root"
        if root_password == "odin":
            self.router_password = a.router_password
        else:
            self.router_password = root_password

    def _reach_bastion(self):
        console_bastion = self.bastion
        try:
            cs_bastion = ConsoleBastion(console_bastion)
            msg = "Success reach Bastion"
            logging.info(msg)
            print(msg)
        except FailConnectBastion:
            logging.error("FailConnectBastion {}".format(console_bastion))
            return False
        host = self.console
        port = self.port
        try:
            cs = ConsoleHost(console_bastion=cs_bastion, host=host, port=port)
            msg = "Success reach Console from Bastion"
            logging.info(msg)
            print(msg)
        except FailConnectConsoleFromBastion:
            msg = ("FailConnectConsoleFromBastion\nconsole: {}\nport: {}\nbastion: {}".format(host, port,\
                                                                                             cs_bastion.console_bastion))
            logging.error(msg)
            print(msg)
            return False
        self.cs = cs
        return True

    def load_console_credential(self, username, password):
        self.console_username = username
        self.console_password = password

    def load_router_credential(self, username, password):
        self.router_username = username
        self.router_password = password

    def _try_connect_console_with_credential(self):
        cs = self.cs
        username = self.console_username
        password = self.console_password
        credential = Credential(username=username, password=password)
        success = cs.login_with_credential(credential)
        return success

    def _load_router(self):
        cs = self.cs
        self.router = Router(console=cs, force_check_root_credential=self.force_check_root_credential, is_new_device=self.is_new_device)

    def _try_connect_router_with_credential(self):
        router = self.router
        if router.connected:
            router.logout()

        username = self.router_username
        password = self.router_password
        credential = Credential(username=username, password=password)

        success = router.login_with_credential(credential)
        return success

    def connect(self):
        if not self._reach_bastion():
            return False
        if not self._try_connect_console_with_credential():
            return False
        self._load_router()
        if self.router.connected and not self.force_check_root_credential:
            print("Success connect to router {}".format(self.router.name))
            return True
        if not self._try_connect_router_with_credential():
            return False
        return True

    def get_router(self):
        return self.router

def get_list_from_file(file):
    result = list()
    with open(file, "r") as f:
        for line in f:
            result.append(line.strip())
    return result

def main():
    parser = argparse.ArgumentParser(description='show and config devices via console')
    parser.add_argument('-d', '--device', help='give device name, e.g. bjs12-vc-edg-r1', required=True)
    parser.add_argument('-r', '--region', help='give region name, e.g. bjs', required=True)
    parser.add_argument('-B', '--bastion', help='give bastion name, e.g. consoles.bjs12')
    parser.add_argument('-CS', '--console', help='give console name, e.g. bjs12-vc-con-r1')
    parser.add_argument('-P', '--port', help='give port name, e.g. 2002')
    parser.add_argument('-CF', '--config_file', help='file with set config list, with each cmd in a line')
    parser.add_argument('-R', '--root_password', help='router root password, default is "Juniper123", or you define the root password')
    parser.add_argument('-S', '--show_file', help='file with show command list, with each cmd in a line')
    parser.add_argument('-SL', '--shell_file', help='file with shell command list like "mkdir", with each cmd in a line')
    parser.add_argument('-L', '--log_file', help='file with record the log and output, default is ~/console-log-devicename-TIMESTAMP.log')
    parser.add_argument('-N', '--is_new_device',
                        help='If it is new deployed Prod vc-edg device, the script will update username, and password with Juniper123',
                        action="store_true")
    parser.add_argument('-SDR', '--set_default_route',
                        help='set default router from interface vme.0 ',
                        action="store_true")

    args = parser.parse_args()
    if args.log_file:
        log_file = args.log_file
    else:
        log_file = log_file_with_device(args.device) # LOG_FILE
    set_logging(log_file)

    force_check_root_credential = False
    is_new_device = False
    if args.is_new_device:
        force_check_root_credential = True
        is_new_device = True
    # print("force_check_root_credential = {}".format(force_check_root_credential))

    if args.root_password:
        root_password = args.root_password
    else:
        root_password = None

    if not args.bastion or not args.port or not args.console:
        cs_info = get_device_console_info(args.device)

        if not cs_info:
            raise ConsoleDBNonAccessible
        bastion = cs_info['bastion']
        console = cs_info['console']
        port = cs_info["port"]
    else:
        bastion = args.bastion
        console = args.console
        port = args.port

    a = Login_Console(device=args.device, region=args.region, bastion=bastion, console=console, port=str(port), root_password=root_password, force_check_root_credential=force_check_root_credential, is_new_device=is_new_device)
    if not a.connect():
        raise WrongConsoleCredential
    # print("Success Login Console with neteng")
    router = a.router
    is_right_device = check_router_name(router.name, args.device, force_same_name = True)

    if is_new_device:
        router.set_root_password()
        
        if router.is_right_default_root_password:
            print("It is the right default root password.")
        else:
            print("Updating root password ...")
            router.set_root_password()
            print("Updated root password.")

        if is_right_device:
            print("It is the right router name.")
        else:
            print("Updating router name ...")
            router.set_router_name(args.device)
            print("Updated router name.")

        # commands for Prod vc-edg
        clis = [
            "deactivate system syslog user *",
            "delete chassis auto-image-upgrade ",
            "set interface vme unit 0 family inet dhcp ",
            "set system services ssh root-login allow protocol-version v2 ",
            # "delete interfaces em0 ",
            # "wildcard range set interfaces et-0/0/[0-70] disable",
        ]
        router.write_configs(clis)

        if args.set_default_route:
            router.set_default_route_from_interface("vme.0")


        router.show_command("show interface vme terse")
        router.show_command("show dhcp client binding interface vme detail | match router ")
        router.show_command("show chassis hardware | match Chassis")

        clis = ["activate system syslog user *"]
        router.write_configs(clis)

    # if not the new device, and wrong device name, exit the script
    else:
        if not is_right_device :
            print("Error {} and {} are different devices".format(router.name, args.device))
            return

    if args.show_file:
        clis = get_list_from_file(args.show_file)
        print("Show clis runing")
        router.show_commands(clis)
        print("show clis completed")

    if args.root_password:  # if use odin password no config
        if args.root_password == "odin":
            return

    if args.shell_file:
        clis = get_list_from_file(args.shell_file)
        print("shell cmd runing")
        router.shell_commands(clis)
        print("shell cmd completed")

    if args.config_file:
        # configs = get_list_from_file(args.config_file)
        # print("Write config runing")
        # router.write_configs(configs)
        # print("Write config completed")
        print("change config TBD, by giving a white list")
        pass

if __name__ == "__main__":
    main()
    #res = get_device_console_info("bjs12-vc-edg-r1")
    #print(res)





