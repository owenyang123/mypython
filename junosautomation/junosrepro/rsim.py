#!/volume/baas_devops/baas/baas_env/bin/python

#
# $Id: rsim.py,v 1.17 2020/11/16 18:19:44 jwania Exp $
#
# This script facilitates executing bsdt regression on a remote server
# from a Baas edit pod.
#
# Supporting scripts:
#   rsim_service.sh
#   rsim_execute.sh
# Configuration file:
#   rsim_server_config.yaml
#
# See rsim_service.sh for directory structure created and used to run bsdt
# regression on remote server.
#
# Copyright (c) 2020 Juniper Networks, Inc.
# All rights reserved.
#
# Authors: Noor Mohamed <noormohamed@juniper.net>, May 2020
#          Prajwal P <pprajwal@juniper.net>
#          Jamsheed Wania <jwania@juniper.net>
#

version="$Revision: 1.17 $"
version_str=version.split(' ')

import sys,os,subprocess,time,shlex,commands,signal,random,re
import uuid
from datetime import datetime
import pytz
from getpass import getuser
from yaml import load, dump, error
from optparse import OptionParser,OptionGroup,IndentedHelpFormatter
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

username=getuser()
prog_name=os.path.basename(__file__)
prog_path=os.path.dirname(os.path.realpath(__file__))

# When addiing a new command line option:
# 1. Update usage string.
# 2. Add handler in parse_options.
# 3. Add options name in valid_options_small and vaild_options_big.
#    and if needed, in permitted_options_list.

usage='Usage: %s [Options] <"command">\n\
Remote Sim: A script to run BSDT on a remote server from a Baas edit pod.\n\
Script will copy all files needed to run BSDT from current sandbox on Baas edit\n\
pod to the remote server, run BSDT and copy back the results to the sandbox on\n\
Baas edit pod.\n\
This is the recommended way to run simparallel on a Baas edit pod, whereas a\n\
single sim or sim in interactive mode can be run directly on the Baas edit pod.\n\
See https://tinyurl.com/yd77rv65 for details on running BSDT from Baas edit pod.\n\
\n\
Options:\n\
  -h, --help       Show this help message and exit.\n\
  -v, --verbose    Display verbose logs.\n\
  -e, --version    Show version and exit.\n\
  -d, --dryrun     Dry run the program.\n\
                   Will turn on verbose logs.\n\
  -s sb_path, --sb-path sb_path\n\
                   Absolute path of sandbox on Baas edit pod, e.g.\n\
                   /baas/username/volume_name/sb_name.\n\
                   Default is $SB.\n\
  -i server:remote_path, --remote-server-path server:remote_path\n\
                   Remote server name and absolute path of sandbox on remote\n\
                   server to run BSDT simulation, e.g.\n\
                   qnc-expubm16-18:/b/username/test_bsdt\n\
                   Default is /b/username/volume_name.\n\
  -k, --keep       Keep BSDT sources and results on remote server.\n\
                   Default is delete.\n\
  -n, --keep-nocp  Keep BSDT sources and results on remote server\n\
                   and skip copying back bsdt results.\n\
                   Default is delete and copy.\n\
  -t, --simreport  Run simreport at the end to show combined results\n\
                   from multiple simparallel invocations.\n\
  -r, --remote-servers\n\
                   List available remote servers for your geo location.\n\
  -g location, --geo location\n\
                   List remote servers in the given geo location (qnc or bng).\n\
\n\
Arguments:\n\
  "command"        BSDT command simparallel with any options in quotes.\n\
\n\
Examples:\n\
  $ %s "simparallel -s qnc" 2>&1 | tee $SB/bsdt.log\n\
  $ %s "simparallel -lu qnc-cosim-1a" 2>&1 | tee $SB/bsdt.log\n\
  $ %s -i qnc-expubm16-11:/b/%s "simparallel -s qnc -l bsdt2"'\
  %(prog_name,prog_name,prog_name,prog_name,username)

parser=OptionParser(usage=usage,conflict_handler="resolve")

def parse_options():
    parser.add_option('-h','--help',              action='store_true',default=False,dest='help',
                        help='null')
    parser.add_option('-e','--ver',               action='store_true',default=False,dest='ver',
                        help='null')
    parser.add_option('-v','--verbose',           action='store_true',default=False,dest='verbose',
                        help='null')
    parser.add_option('-d','--dryrun',            action='store_true',default=False,dest='dry_run',
                        help='null')
    parser.add_option('-s','--sb-path',           action='store',     type='string',dest='sb_path',
                        help='null')
    parser.add_option('-i','--remote-server-path',action='store',     type='string',dest='remote_server_path',
                        help='null')
    parser.add_option('-k','--keep',              action='store_true',default=False,dest='keep',
                        help='null')
    parser.add_option('-n','--keep-nocp',         action='store_false',default=True,dest='copy',
                        help='null')
    parser.add_option('-t','--simreport',         action='store_true',default=False,dest='simreport',
                        help='null')
    parser.add_option('-r','--remote-servers',    action='store_true',default=False,dest='show_remote_servers',
                        help='null')
    parser.add_option('-g','--geo',               action='store',     type='string',dest='geo',
                        help='null')

    parser.disable_interspersed_args()
    return parser.parse_args()

def this_def_name():
    return sys._getframe(1).f_code.co_name

def preparse_options():
    valid_options_small=['h','e','v','d','s','i','k','n','t','r','g']
    valid_options_big=['help','ver','verbose','dryrun','sb-path','remote-server-path','keep','keep-nocp','simreport','remote-servers','geo']
    valid_options_with_arg=['-s','--sb-path','-i','--remote-server-path','-g','--geo']
    n=len(sys.argv)
    for i in range(1,n):
        # Validate arguments and set the correct number of hyphens (- or --) before
        # arguments which start with a hyphen.
        if sys.argv[i][0]=='-':
            obj=re.search(r'[^\-]',sys.argv[i])
            if not obj:
                print('\nERROR: \"%s\" is not a not vaild argument\n' %(sys.argv[i]))
                print(usage)
                sys.exit(1)
            # Strip of '-'s from argv and verfiy with the list. If argv is a valid option, prepend
            # stripped argv with - for single character argv, and -- for multi-character argv.
            # obj.start() returns the index of the start of the substring matched.
            # If sys.argv[i] = "-h",     obj.start() = 1
            # If sys.argv[i] = "--help", obj.start() = 2
            # sys.argv[i][obj.start():] returns sys.argv[i] from character obj.start() to the end.
            stripped_arg=sys.argv[i][obj.start():]
            if stripped_arg in valid_options_small:
                sys.argv[i]='-'+stripped_arg
            elif stripped_arg in valid_options_big:
                sys.argv[i]='--'+stripped_arg
            else:
                print('\nERROR: \"%s\" is not a vaild argument\n' %(sys.argv[i]))
                print(usage)
                sys.exit(1)
        else:
            # If a non hyphenated command line option does not follow an option
            # which has an argument and if it is not "command", then it is an
            # invalid option.
            if not sys.argv[i-1] in valid_options_with_arg:
                obj=sys.argv[i].split()
                if obj[0]!='simparallel':
                    print('\nERROR: \"%s\" is not a vaild argument\n' %(sys.argv[i]))
                    print(usage)
                    sys.exit(1)

# PR 1501607 fix is needed to run bsdt correctly on xxx-expubm16-NN servers.
def validata_pr_1501607():
    global dry_run,sb_path
    rpio_filename=("%s/src/pfe/common/drivers/rpio/rpio_client.c" %(sb_path))
    if not os.path.isfile(rpio_filename):
        print("\nERROR: File %s not found" %(rpio_filename))
        print("ERROR: Env var $SB or sb path provided via -s option does not point to a valid sandbox")
        print("ERROR: Please set $SB, provide sb path via -s option or run from within a sandbox\n")
        sys.exit(1)
    cmd=("grep '#undef memmove' %s > /dev/null" %(rpio_filename))
    r=os.system(cmd)
    if r!=0:
        # '#undef memmove' not found indicating fix is not present
        print("\nWarning: PR 1501607 fix to run bsdt correctly on xxx-expubm16-NN servers missing in")
        print("  %s" %(rpio_filename))
        print("Patch GRN 1101134 in sb first, then build and run bsdt.")
        print("To generate patch: svn diff svn+ssh://svn@svl-svn.juniper.net/junos-2009 -c 1101134\n")
        user_choice=query_yes_no('Do you want to continue?', 'no')
        if not user_choice:
            if dry_run:
                print('Program completed')
            sys.exit(1)

def validate_options():
    global command,dry_run,geo,keep,log_path,copy,remote_path,remote_server_path,sb_path,show_remote_servers,simreport,user_command,verbose
    command=''
    geo=''
    keep=''
    log_path=''
    remote_path=''
    remote_server_path=''
    show_remote_servers=options.show_remote_servers
    permitted_options_list=['-v','--verbose','-d','--dryrun','-g','--geo','-k','--keep','-n','--keep-nocp','-t','--simreport']
    if options.geo:
	geo=options.geo
        if (geo!="qnc" and geo!="bng"):
            print('\nERROR: "%s" is not a valid geo location\n' %(geo))
            print(usage)
            sys.exit(1)
    if show_remote_servers:
	return
    n=len(sys.argv)
    # Look for bsdt command
    if n>1 and (sys.argv[1]=='-h' or sys.argv[1]=='--help'):
        print(usage)
        sys.exit(0)
    elif n>1 and (sys.argv[1]=="-e" or sys.argv[1]=='--ver'):
        print"Version", version_str[1]
        sys.exit(0)
    elif n>1 and sys.argv[n-2][0]!='-' and sys.argv[n-1][0]!='-':
        # rsim.py -s /baas/username/volume_name/sb_name "simparallel -s qnc"
        command=sys.argv[n-1]
    elif n>1 and sys.argv[n-2] in permitted_options_list and sys.argv[n-1][0]!='-':
        # rsim.py -k "simparallel -s qnc"
        command=sys.argv[n-1]
    else:
        # Set a default command if none is specified on the command line. Not doing this for now.
        #geo=subprocess.check_output(['/volume/buildtools/bin/sb-query', '--sbsite']).rstrip()
        #command=("simparallel -s %s" %(geo))
        print('\nERROR: "command" must be the last argument on the command line\n')
        print(usage)
        sys.exit(1)
    # Save argument "command"
    user_command=command
    command_list=command.split()
    if command_list[0]!='simparallel':
        print('\nERROR: BSDT command "%s" not supported\n' %(command_list[0]))
        print(usage)
        sys.exit(1)
    copy=options.copy
    if copy:
        keep=options.keep
        simreport=options.simreport
    else:
        keep=True
        simreport=False
    dry_run=options.dry_run
    if dry_run:
        verbose=dry_run
    else:
        verbose=options.verbose
    if options.sb_path:
        # Strip any trailing /
        sb_path=options.sb_path.rstrip('/')
    else:
        if 'SB' in os.environ:
            sb_path=os.environ['SB']
        else:
            # Create sb_path if within a sb
            cmd=("/volume/pfetools/ws_topdir")
            output=os.popen(cmd).read().split()[0]
            if output == "ERROR":
                print('ERROR: Please set $SB, provide sb path via -s option or run from within a sandbox')
                sys.exit(1)
            else:
                # Script is running from within a sb
                sb_name=output.split('/')[-1]
                vol_path=os.popen("/volume/baas_devops/bin/baas ls --current-vol-path").read().rstrip()
                sb_path=vol_path+'/'+sb_name
                print_output("sb_path formed from current sandbox: %s" %(sb_path))
                cmd=wrap('[ -d %s ] || echo False' %(sb_path))
                output=os.popen(cmd).read().split()
                if output=="False":
                    print("ERROR: sb_path formed from current sb %s does not exist" %(sb_path))
                    print('ERROR: Please set $SB, provide sb path via -s option or run from within a sandbox')
                    sys.exit(1)

    cmd=wrap('[ -d /b/workspace ] && df -BG /b/workspace || echo False')
    output=os.popen(cmd).read().split()
    if output[0]=="False":
        print('ERROR: %s is only expected to run on a Baas edit pod' %(prog_name))
        sys.exit(1)

    # Warn user not to use /b/workspace path in SB
    sb_string=sb_path.split('/')
    if len(sb_string)<3:
        print("ERROR: SB=%s" %(sb_path))
        print("ERROR: SB path does not seem to match format SB=/baas/username/volume_name/sandbox_name")
        sys.exit(1)
    if sb_string[2]=="workspace":
        print("ERROR: SB=%s" %(sb_path))
        print("ERROR: Please set SB=/baas/username/volume_name/sandbox_name or")
        print("ERROR: unset SB if running script from within a sandbox.")
        sys.exit(1)


    if options.remote_server_path:
        remote_server_path=options.remote_server_path

    # PR 1501607 fix is needed to run bsdt on xxx-expubm16-NN servers.
    validata_pr_1501607()

def wrap(cmd):
    # Wrap the command in /bin/sh.
    # If it is a non bash user, expression return errors.
    # That's why wrapping is required.
    return "/bin/sh -c \'%s\'" %(cmd)

def add_ssh(cmd,server):
    return "ssh -q %s \"%s\""  %(server,cmd)

def handle_keyboard_int(remote_server,unqid,def_name):
    try:
        global dry_run,remote_path,sb_name,sb_path,tarfile
        print('\nKeyboard interrupt in def %s()' %(def_name))
        print('Terminating processes')
        if not dry_run:
            # Execute_cmd will be running in background, find and kill the process
            cmd=wrap("[ -f %s/process-%s ]  && pkill -P $(cat %s/process-%s) || :" %(sb_path,unqid,sb_path,unqid))
            os.popen(cmd)
            # Search if file was created with uuid and kill the process
            cmd=add_ssh(wrap('[ -f %s/%s/%s/process ] && pkill -P $(cat %s/%s/%s/process) || :' %(remote_path,sb_name,unqid,remote_path,sb_name,unqid)),remote_server)
            output=subprocess.check_output(shlex.split(cmd))
            cleanup_files(unqid,tarfile)
        if dry_run:
            print('Program completed')
        sys.exit(1)
    except KeyboardInterrupt:
        handle_keyboard_int(remote_server,unqid,"handle_keyboard_int")
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def handle_keyboard_int()")
        sys.exit(1)

def query_yes_no(question, default="no"):
    valid={"yes": True, "ye": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt=" [y/n] "
    elif default == "yes":
        prompt=" [y/n] "
    elif default == "no":
        prompt=" [y/n] "
    else:
        raise ValueError("Invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice=raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def execute_shell(current_vol_path,unqid):
    global command,dry_run,log_dir,log_path,copy,remote_path,remote_server,sb_name,simreport,tarfile,user_command,verbose
    try:
        rsim_service_path=prog_path+'/rsim_service.sh'
        tarfile='%s-%s.tar' %(sb_name,unqid)
        cmd='%s %s %s:%s "%s" "%s" %s %s %s %s %s %s %s %s' %(rsim_service_path,current_vol_path,remote_server,remote_path,user_command,command,log_dir,log_path,unqid,tarfile,verbose,dry_run,copy,simreport)
        if verbose or dry_run:
            print ("%s" % (cmd))
        args=shlex.split(cmd)
        process=subprocess.Popen(args)
        process.wait()
        cleanup_files(unqid,tarfile)
        if dry_run:
            print('Program completed')
    except KeyboardInterrupt:
        process.terminate()
        process.kill()
        handle_keyboard_int(remote_server,unqid,"execute_shell")
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def execute_shell()")
        sys.exit(1)

#
# 'vmstat 1 2; df -BG /b' generates this output:
#
#   procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----      <-- output[0]
#    r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
#    1  0      0 31094860 250396 1182196    0    0     3     1   10   16  0  0 100  0  0
#    0  0      0 31095136 250396 1182196    0    0     0     0  115  161  0  0 100  0  0  <-- output[3]
#   Filesystem         1G-blocks  Used Available Use% Mounted on
#   /dev/mapper/data-b     4032G  130G     3698G   4% /b                                  <-- output[-2]
#
# The 6 lines are placed in output[0] to output[6], with output[6] being a blank line.
# output[3] and output[-2] lines are pointed out above.
# output[3][14] = 100 and output[-2][3][:-1] = 3698.
#

def get_remote_server_stats(remote_server):
    try:
        cmd=wrap("ping -c 2 %s" %(remote_server))
        args=shlex.split(cmd)
        # Will continue at except if ping fails
        output=subprocess.check_output(args).split('\n')

        cmd=add_ssh(wrap('vmstat 1 2; df -BG /b'),remote_server)
        args=shlex.split(cmd)
        output=subprocess.check_output(args).split('\n')
        cpu_usage=100-int(output[3].split()[14])
        available_space=int(output[-2].split()[3][:-1])
        return 0,cpu_usage,available_space

    except Exception as exc:
        # ping failed, return code rc=1
        return (1,0,0)

def get_remote_server(remote_servers_list,max_cpu,required_space):
    try:
        global dry_run
        remote_servers_list=random.sample(remote_servers_list, len(remote_servers_list))
        if dry_run:
            return remote_servers_list[0]
        while True:
            # Check if any of the remote servers have more than specified disk space and cpu
            # load not more than specified cpu load, otherwise try indefinetly.
            for remote_server in remote_servers_list:
                # Get real time cpu usage and disk usage, verify with the config
                (rc,cpu_usage,available_space)=get_remote_server_stats(remote_server)
                if rc==0 and cpu_usage<max_cpu and available_space>required_space:
                    return remote_server
            print('ERROR: All remote servers are either busy or lack sufficient disk space.')
            print('Waiting for remote servers to be free.')
            time.sleep(30)

    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def get_remote_server()")
        sys.exit(1)

def remote_server_cpu_disk_usage(remote_servers_list):
    try:
        tz_SF=pytz.timezone('US/Pacific')
        datetime_SF=datetime.now(tz_SF)
        datetime_str=datetime_SF.strftime("%a %b %d %H:%M:%S")
        print("\n%s" %(datetime_str))
        t_start=time.time()
        print("Server          | CPU usage % | Available Space GB | Elapsed Time sec")
        for remote_server in remote_servers_list:
            # Get real time cpu usage and disk usage, verify with the config
            t0=time.time()
            (rc,cpu_usage,available_space)=get_remote_server_stats(remote_server)
            t1=time.time()
            if rc==0:
                elapsed_time=t1-t0
                print("%14s | %3d         | %6d             |  %d"
                        %(remote_server,cpu_usage,available_space,elapsed_time))
            else:
                print("%14s | Unreachable |" %(remote_server))
        t_end=time.time()
        elapsed_time=t_end-t_start
        elapsed_time_str=("%d min %d sec" %(elapsed_time/60,elapsed_time%60))
        datetime_SF=datetime.now(tz_SF)
        datetime_str=datetime_SF.strftime("%a %b %d %H:%M:%S")
        print("%s, Elapsed time: %s" %(datetime_str,elapsed_time_str))

    except KeyboardInterrupt:
        print('\nKeyboard interrupt in def remote_server_cpu_disk_usage()')
        print('Terminating program')
        sys.exit(1)
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def remote_server_cpu_disk_usage()")
        sys.exit(1)

def cleanup_files(unqid,tarfile):
    try:
        global dry_run,keep,remote_path,remote_server,sb_name,sb_path
        if not dry_run:
            # Don't delete the sb if more than one unqid process file is present in sb on remote server
            cmd=add_ssh(wrap('ls %s/%s/unq-*/process | wc -l' %(remote_path,sb_name)),remote_server)
            with open(os.devnull, 'w') as devnull:
                output=subprocess.check_output(shlex.split(cmd), stderr=devnull).split('\n')
            if int(output[0])>1:
                keep=True
        if keep:
            # Delete unqid process file and tarfile on remote server, don't delete the remote sb
            cmd=add_ssh(wrap('rm -rf %s/%s/%s/process %s/%s' %(remote_path,sb_name,unqid,remote_path,tarfile)),remote_server)
            print_output(cmd)
            print("When no longer needed, please delete %s:%s/%s using" %(remote_server,remote_path,sb_name))
            print("ssh -q %s \"rm -rf %s/%s\"" %(remote_server,remote_path,sb_name))
        else:
            # Delete sb and tarfile on remote server
            cmd=add_ssh(wrap('rm -rf %s/%s %s/%s' %(remote_path,sb_name,remote_path,tarfile)),remote_server)
            print_output(cmd)

        if not dry_run:
            output=subprocess.check_output(shlex.split(cmd))

        # Delete temp directory (where tar file was created) and process file on local sb
        cmd=wrap('rm -rf %s/%s %s/process-%s' %(sb_path,unqid,sb_path,unqid))
        print_output(cmd)
        if not dry_run:
            output=subprocess.check_output(shlex.split(cmd)).split('\n')
    except KeyboardInterrupt:
        handle_keyboard_int(remote_server,unqid,"cleanup_files")
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def cleanup_files()")
        sys.exit(1)

# Process BSDT command
def process_command(unqid):
    try:
        global command,log_dir,log_path,remote_path,sb_name,sb_path
        command_list=command.split()
        # If log directory is mentioned, validate if path exists
        if ' -l ' in command:
            log=command_list[command_list.index('-l')+1]
            if len(log.split('/'))>1:
                log_path='/'.join(log.split('/')[:-1])
                cmd=wrap('[ -d %s ] && echo True || echo False' %(log_path))
                output=os.popen(cmd).read().split()[0]
                if output == "False":
                    print('ERROR: %s path doesn\'t exist' %(log_path))
                    sys.exit(1)
                log_dir=log.split('/')[-1]
            else:
                log_path=sb_path
                log_dir=log.split('/')[0]
            # Replace the log path
            command_list[command_list.index('-l')+1]='%s/%s/%s/%s' %(remote_path,sb_name,unqid,log_dir)
        else:
            log_path=sb_path
            log_dir='bsdt'
            command_list.insert(1,'-l %s/%s/%s/%s' %(remote_path,sb_name,unqid,log_dir))

        if ' -p ' in command:
            # Loop to replace sb_path/.../pkg.xml with remote_path/.../pkg.xml, sanity
            # check pkg file name (add .xml extension if missing) and check if file exists.
            test_path_local=("%s/src/pfe/ucode/lu/scripts/test" %(sb_path))
            test_path_remote=("%s/%s/src/pfe/ucode/lu/scripts/test" %(remote_path,sb_name))
            n=len(command_list)
            for i in range(1,n):
                #print_output("Command arg: n %d, i %d, arg %s" %(n,i,command_list[i]))
                if command_list[i]=="-p":
                    if i==n-1:
                        # Last argument in "command"
                        print('ERROR: -p missing argument')
                        sys.exit(1)
                    if command_list[i+1][0]=='-':
                        print('ERROR: -p followed by hyphenated option %s' %(command_list[i+1]))
                        sys.exit(1)
                    xml_file=os.path.basename(command_list[i+1])
                    xml_filename,xml_extension=os.path.splitext(xml_file)
                    if xml_extension!=".xml":
                        print_output('Package name "%s" missing .xml extension' %(xml_file))
                        xml_file=xml_file+".xml"
                        print_output('Package name is "%s" after adding .xml' %(xml_file))
                    fname=("%s/%s" %(test_path_local,xml_file))
                    if os.path.exists(fname) and os.path.isfile(fname):
                        command_list[i+1]=("%s/%s" %(test_path_remote,xml_file))
                    else:
                        print('ERROR: Package file "%s" does not exist' %(command_list[i+1]))
                        sys.exit(1)
        command=' '.join(command_list)
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def process_command()")
        sys.exit(1)


def print_output(out):
    global verbose
    if verbose:
        print(''+str(out))
        sys.stdout.flush()

def initialize_setup():
    try:
        if not show_remote_servers:
            if dry_run:
                print("Dry run")
            print("Initializing setup")
            sys.stdout.flush()
        global copy,geo,keep,remote_path,remote_server,sb_name,sb_path,simreport,username
        unqid='unq-'+str(uuid.uuid4().hex[:6])
        # Fetch remote server names
        remote_servers_path=prog_path+'/rsim_server_config.yaml'
        data=load(file(remote_servers_path, 'r') , Loader=Loader)
        max_cpu=data['max_cpu']
        required_space=data['required_space']

        # Use geo location specified on command line or check the sb's location and
        # select geo based remote servers pool.
	if not geo:
	    geo=subprocess.check_output(['/volume/buildtools/bin/sb-query', '--sbsite']).rstrip()
        remote_servers_list=data[geo]
        if show_remote_servers:
            print('\n'.join(remote_servers_list))
            remote_server_cpu_disk_usage(remote_servers_list)
            sys.exit(0)

        # Check if current volume has enough space to copy back bsdt log
        if not dry_run:
            cmd=wrap('[ -d /b/workspace ] && df -BG /b/workspace || echo False')
            output=os.popen(cmd).read().split()
            if output[0]=="False":
                print('ERROR: %s is only expected to run on a Baas edit pod' %(prog_name))
                sys.exit(1)
            # Skip check if no copy is used
            if copy:
                # if output is
                #   Filesystem     1G-blocks  Used Available Use% Mounted on
                #   /dev/sdo           1477G  367G     1110G  25% /b/workspace
                #                                      -3     -2  -1
                # output[-3]       = 1110G
                # output[-3][:-1]  = 1110
                available_space=int(output[-3][:-1])
                if available_space<required_space:
                    print("WARNING: Only %sG space is left in your volume" %(available_space))
                    print("WARNING: BSDT test may fail while copying back logs")
                    user_choice=query_yes_no('Do you want to continue?', 'no')
                    if not user_choice:
                        if dry_run:
                            print('Program completed')
                        sys.exit(1)

        # Construct remote server path if not provided
        if remote_server_path and ':' in remote_server_path:
            remote_server,remote_path=remote_server_path.split(':')
            (rc,cpu_usage,available_space)=get_remote_server_stats(remote_server)
            if rc!=0:
                print("ERROR: Remote server %s unreachable" %(remote_server))
                sys.exit(1)
            if available_space<required_space:
                print("WARNING: Only %sG space is left on remote server:%s" %(available_space,remote_server))
                print("WARNING: BSDT test may fail")
                user_choice=query_yes_no('Do you want to continue?', 'no')
                if not user_choice:
                    if dry_run:
                        print('Program completed')
                    sys.exit(1)
        elif remote_server_path and ':' not in remote_server_path:
            remote_path=remote_server_path
            print_output('Determining remote server')
            t0=time.time()
            remote_server=get_remote_server(remote_servers_list,max_cpu,required_space)
            t1=time.time()
            elapsed_time=t1-t0
            print_output("Determining remote server took: %d min %d sec" %(elapsed_time/60,elapsed_time%60))
        else:
            vol=os.popen("/volume/baas_devops/bin/baas ls --current-vol").read().rstrip()
            remote_path='/b/'+username+'/'+vol
            print_output('Determining remote server')
            t0=time.time()
            remote_server=get_remote_server(remote_servers_list,max_cpu,required_space)
            t1=time.time()
            elapsed_time=t1-t0
            print_output("Determining remote server took: %d min %d sec" %(elapsed_time/60,elapsed_time%60))

        # Verify the path and remove extra path
        if 'SB' in os.environ:
            print_output("Env var SB=%s" %(os.environ['SB']))
            sb_name= os.environ['SB'].rstrip('/').split('/')[-1]
            print_output("SB name=%s" %(sb_name))
        else:
            sb_path='/'.join(sb_path.split('/')[0:5])
            sb_name=sb_path.split('/')[-1]

        # Determine namespace of Baas edit pod. When logged into another user's Baas
        # edit pod using "baas edit -s userA/volume_name", and running bsdt
        # from userA's Baas edit pod, three options need to be overridden.
        # 1. copy needs to be False as the user running bsdt will not have permission
        #    to copy over the results in the userA's directory.
        # 2. keep is set to True to keep the temp dir on remote server instead of deleting
        #    it. User will need to manually delete the temp dir on remote server.
        # 3. simreport is also set to False as it makes no sense to run it when there is
        #    only one bsdt run.
        # These are the same as if user had specified --keep-nocpy option.
        # For sb_path=/baas/userA/volume_name/sb_name, sb_path_str[2]=userA.
        sb_path_str=sb_path.split('/')
        namespace=sb_path_str[2];
        string='SB path and namespace: %s %s' %(sb_path,namespace)
        print_output(string)
        if username!=namespace:
            copy=False
            keep=True
            simreport=False

        # Process BSDT command
        process_command(unqid)
        execute_shell(sb_path,unqid)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt in def initialize_setup()')
        print('Terminating program')
        sys.exit(1)
    except Exception as exc:
        print("Exception: %s" %(exc))
        print("Failed in def initialize_setup()")
        sys.exit(1)

def log_datetime():
    # Open file in append mode
    fname="/homes/jwania/rsim_log.txt"
    if os.path.exists(fname) and os.path.isfile(fname):
        fd=open(fname, "a")
        if fd:
            tz_SF=pytz.timezone('US/Pacific')
            datetime_SF=datetime.now(tz_SF)
            datetime_str=datetime_SF.strftime("%Y/%m/%d %H:%M:%S")
            fd.write("%s  %-15s %s\n" %(datetime_str,username,sys.argv[1:]))
            fd.close()

def main():
    """Main Function"""
    global options
    log_datetime()
    preparse_options()
    (options,arg)=parse_options()
    validate_options()
    initialize_setup()
    sys.exit(0)

if __name__ == '__main__':
    main()
