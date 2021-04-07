#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import dxd_tools_dev.modules.pttv2_cli_module as pttv2_cli

def main():
    pttv2_cli.main_process_loop()

if __name__ == '__main__':
    main()

