#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

from dxd_tools_dev.modules import port_testing_cli

def main():
    port_testing_cli.main_process_loop()

if __name__ == '__main__':
    main()

