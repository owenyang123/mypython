#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

"""
DA Script CLI, is a tool to run script defined in a template file.

Version   Date         Author     Comments
1.00      2020-07-07   wanwill@   Initial version
1.01      2020-07-10   wanwill@   update some wording and format
"""

import getpass
from dxd_tools_dev.modules.da_script import run_var

import os
from cmd import Cmd

def get_user():
    return os.getlogin()

class Command(Cmd):
    intro = ">> Welcome to Deployment Assistant Script\n"
    prompt = "(DAScript)> "

    user = None
    password = None

    def help_login(self):
        print("format : login existing_user")

    def do_login(self, line):
        if "?" in line:
            self.help_login()
            return
        self.user = get_user()

        indication = f"please input password of {self.user}: "
        self.password = getpass.getpass(indication)
        print("The password is stored.\n")
        return

    def help_run(self):
        print("format: 'run ~/example_paths/varfile.var'")

    def do_run(self, line):
        if "?" in line:
            self.help_run()
            return
        var_file_name = line.strip()
        print(f"var_file_name is {var_file_name}")
        run_var(var_file_name, self.password)
        return

    def help_help(self):
        print("run          Run a var file")
        print("login        Login, and script will ask you input password")
        print("exit         Exit DA Script")
        print("help cmd     Get help info of this cmd. e.g 'help run' get help info of run cmd\n")

    def do_help(self, line):
        help_word = line.strip()
        if help_word == "run":
            self.help_run()
            return
        if help_word == "login":
            self.help_login()
            return
        self.help_help()

    def emptyline(self):
        return

    def do_EOF(self, line):
        return True

    def do_exit(self, line):
        return self.do_EOF(line)

def loop():
    Command().cmdloop()

if __name__ == '__main__':
    loop()

