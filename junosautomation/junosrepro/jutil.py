from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.start_shell import StartShell
from lxml import etree
import os
import logging
import sys
import time

logging.addLevelName(25, "NORMAL")
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s: %(module)s [%(funcName)s] [%(process)s] [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=25)


def Configure(dev, config):
    """
    Configuration module based on PyEz and Netconf.
    """
    cu = Config(dev)
    cu.load(config, format="set", merge=True)
    cu.commit(comment="PyEZ @ E.Schornig.")
    time.sleep(5)
    logging.log(25, "Commited config to device: {}".format(dev.facts['hostname']))


def get_cli_cmd(dev, cmd, pipe=None):
    """
    Will return the text output of cli command.

    Args:
        dev: open ssh connection to a Juniper router.
        cmd: Juniper cli command

    Return:
        cmd_output: text output of a cli command.
    """
    cmd_output = ''
    logging.log(25, 'Sending CLI: [{}] to [{}].'.format(cmd,
                dev.facts['hostname']))
    rpc_reply = dev.rpc.cli(cmd)
    output = etree.tostring(rpc_reply)
    with open('tmp_output', 'w+') as f:
        f.write(output)
        f.seek(0)
        for line in f.readlines():
            if not (line.startswith('<') and line.endswith('>\n')):
                if pipe:
                    for arg in pipe:
                        if arg in line:
                            cmd_output += line
                else:
                    cmd_output += line
    os.remove('tmp_output')
    return cmd_output


def config_save(dev, location=None, config_format=None):
    """
    Saves configuration file for a Juniper device.

    Args:
        dev: open ssh connection to a Juniper router.
        location: local path where the config should be saved. If no location
                  is provided we will use the curent directory.
        style:
              default: curly brackets a.k.a Juniper style.
              set: saves the config in set format

    Returns:
        None
    """
    logging.log(25, 'Saving config: location={}, config_format={}.'.format(
                location, config_format))
    # Check if we need to save the config in a special format.
    if config_format is None:
        cmd = 'show configuration'
    elif config_format == 'set':
        cmd = 'show configuration | display set'

    # Fetch the configuration
    logging.log(25, 'Fetching config for [{}]'.format(dev.facts['hostname']))
    config = get_cli_cmd(dev, cmd)
    config_file_name = '{}.cfg'.format(dev.facts['hostname'])

    # Normalize the hostname for dual RE devices.
    if 're0' in config_file_name:
        config_file_name = config_file_name.replace('re0', '')
    elif 're1' in config_file_name:
        config_file_name = config_file_name.replace('re1', '')

    # Check if location has been provided.
    # Create the directory structure if it does not exist.
    if location:
        if location.endswith('/'):
            config_file_name = location + config_file_name
        else:
            config_file_name = location + '/' + config_file_name
        if os.path.exists(location) is False:
            logging.log(25, 'Destination folder does not exist.')
            logging.log(25, 'Creating folder: [{}].'.format(location))
            os.makedirs(location)

    # Write configuration to file.
    with open(config_file_name, 'w+') as f:
        f.write(config)
    logging.log(25, 'Finished saving config to [{}].'.format(config_file_name))
    return None


def run_cli(dev, cmd):
    dev_shell = StartShell(dev)
    dev_shell.open()
    output = str()
    if type(cmd) == str:
        output = dev_shell.run('cli -c "{}"'.format(cmd))[1]
        logging.log(25, 'Sending CLI: [{}] to [{}].'.format(cmd, dev.facts['hostname']))
    elif type(cmd) == list:
        for entry in cmd:
            output += dev_shell.run('cli -c "{}"'.format(entry))[1]
            logging.log(25, 'Sending CLI: [{}] to [{}].'.format(entry, dev.facts['hostname']))
    dev_shell.close()
    return output


def run_shell(dev, cmd):
    dev_shell = StartShell(dev)
    dev_shell.open()
    if type(cmd) == str:
        dev_shell.run('{}'.format(cmd))
        logging.log(25, 'Sending shell: [{}] to [{}].'.format(cmd, dev.facts['hostname']))
    elif type(cmd) == list:
        for entry in cmd:
            dev_shell.run('{}'.format(entry))
            logging.log(25, 'Sending shell: [{}] to [{}].'.format(entry, dev.facts['hostname']))
    dev_shell.close()


def connect(ip, user, password, facts=True):
    """
    Open a connection to Juniper Device.

    Args:
        ip: target device ip address
        user/password: ssh credentials

    Returns:
        dev: open ssh connection to Juniper Device.
    """
    dev = Device(host=ip, user=user, passwd=password, facts=True)
    logging.log(25, 'Connecting to device IP: [{}].'.format(ip))
    dev.open()
    logging.info(25, 'OK. Connected to [{}].'.format(dev.facts['hostname']))
    return dev


def main():
    pass

if __name__ == '__main__':
    main()
