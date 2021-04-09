#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"
from __future__ import print_function, unicode_literals
import git, os, logging, sys, re, subprocess, ipaddress, datetime, argparse
from importlib import reload
from pathlib import Path


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HIGHGREEN = "\033[1;42m"


def parse_args():
    """Parse args input by user and help display"""
    parser = argparse.ArgumentParser ( description='''IP Validation for border side on 'GenevaBuilder','GenevaBuilderDCEdge','GenevaBuilderDCNE' && Herclues and the Regions border CORs \n
    wiki:TBD
    Examples:
    /apollo/env/DXDeploymentTools/bin/ipv.py -i 99.78.186.38/32,99.78.186.39/32,99.78.186.40/32,99.78.186.41/32,99.78.186.42/32,99.78.186.43/32,99.78.186.44/32 -r icn 
    ''', add_help=True, formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument ( '-i', '--ips', required=True, dest='ips',
                          help='list of ips with CIDR notation ( a.b.c.d/e,f.g.h.i/j (comma-separated)' )
    parser.add_argument ( '-r', '--region', required=True, dest='region', help='region code iad,dub,nrt,.....' )
    return parser.parse_args()


def setup_logging(verbosity_level):
    logging.shutdown ()
    reload ( logging )

    logging.basicConfig (  # filename='example.log',
        # format='%(asctime)s [%(levelname)s] %(funcName)s - %(message)s',
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        filemode='w', level=verbosity_level )
    logging.addLevelName ( logging.INFO, "\033[36m%s\033[1;0m" % logging.getLevelName ( logging.INFO ) )
    logging.addLevelName ( logging.WARNING, "\033[33m%s\033[1;0m" % logging.getLevelName ( logging.WARNING ) )
    logging.addLevelName ( logging.ERROR, "\033[31m%s\033[1;0m" % logging.getLevelName ( logging.ERROR ) )


def git_clone(package, path="/home/"+os.getlogin ()+"/"):
    full_path = path+package
    full_url = 'ssh://git.amazon.com/pkg/'+package
    try:
        repo = git.Repo.clone_from ( full_url, to_path=f'{full_path}' )
        return repo
    except:
        logging.error ( 'Could not clone {}. Exception {}'.format ( package, sys.exc_info () ) )
        return None


def repo_creation(reponame):
    username = os.getlogin ()
    if os.path.exists ( f'/home/{username}/{reponame}/' ) == True:
        repo = git.Repo ( f'/home/{username}/{reponame}' )
        origin = repo.remote ( 'origin' )
        logging.info ( f'{reponame} repo exists' )
        logging.info ( f'git pull for {reponame}' )
        origin.pull ()
        logging.info ( f'git pull for {reponame} done' )
    else:
        logging.info ( f'{reponame} repo does not exist' )
        logging.info ( f'Performing git clone on {reponame}' )
        cloned = git_clone ( f'{reponame}' )

        if cloned:
            logging.info ( f'git clone successful for {reponame}' )
            repo = git.Repo ( f'/home/{username}/{reponame}' )
            origin = repo.remote ( 'origin' )
            logging.info ( f'git pull for {reponame}' )
            origin.pull ()
            logging.info ( f'git pull for {reponame} done' )
        else:
            logging.error ( f'git clone failed for {reponame}, Please Clone Manually and then re-run the script' )
            sys.exit ()


def getListOfFiles(repodir):
    listOfFile = os.listdir ( repodir )
    allFiles = list ()
    for entry in listOfFile:
        fullPath = os.path.join ( repodir, entry )
        if os.path.isdir ( fullPath ):
            allFiles = allFiles+getListOfFiles ( fullPath )
        else:
            allFiles.append ( fullPath )
    return allFiles


def region_cor(region):
    GBrepo_targetspec = home+"/GenevaBuilder/targetspec/border"
    try:
        completed_process = subprocess.run ( f'ls {GBrepo_targetspec} | grep br-cor-r1 | grep {region}', shell=True,
                                             stdout=subprocess.PIPE )
        output = completed_process.stdout
        output = output.decode ( 'ascii' ).split ( '\n' )
        cor = output[ 0 ]
        return cor
    except Exception as e:
        logging.error ( "Could not get cor device from GB" )
        logging.error ( e )
        sys.exit ()


def ipv_bastions(region, ips):
    myCommand = [
        f'/apollo/env/NetengAutoChecks/bin/autochecks_manager --no-login-prompt --checks routes.check_ip_prefix_longer_not_exist --target iad2-br-cor-r1 --prefix {ips}',
        f'/apollo/env/NetengAutoChecks/bin/autochecks_manager --no-login-prompt --checks routes.check_ip_prefix_longer_not_exist --target gru3-br-cor-r1 --prefix {ips}',
        f'/apollo/env/NetengAutoChecks/bin/autochecks_manager --no-login-prompt --checks routes.check_ip_prefix_longer_not_exist --target syd1-br-cor-r1 --prefix {ips}',
        f'/apollo/env/NetengAutoChecks/bin/autochecks_manager --no-login-prompt --checks routes.check_ip_prefix_longer_not_exist --target dub2-br-cor-r1 --prefix {ips}' ]
    bastions = [ 'nebastion-iad', 'nebastion-gru', 'nebastion-syd', 'nebastion-dub' ]

    if region not in [ 'iad', 'gru', 'dub', 'syd' ]:
        cor = region_cor ( region )
        bastions.append ( f'nebastion-{region}' )
        myCommand.append (
            f'/apollo/env/NetengAutoChecks/bin/autochecks_manager --no-login-prompt --checks routes.check_ip_prefix_longer_not_exist --target {cor} --prefix {ips}' )

    for i, command in enumerate ( myCommand ):
        for j, host in enumerate ( bastions ):
            if i == j:
                logging.info ( f'>> connecting to {host} ... ' )
                subprocess.call ( [ 'ssh', '-t', host, command ] )


def SCRAP_repo_FILE(repofiles, pattern):
    try:
        scrap = open ( repofiles, "r", encoding="ISO-8859-1" )
        regex = re.compile ( pattern )
        matched_lines = list ()
        for line in scrap:
            if regex.findall ( line ):
                matched_lines.append ( line )
                break
        return (matched_lines)
        scrap.close ()
    except Exception as e:
        logging.error ( "Exception:SCRAP_repo_FILE:{}".format ( str ( e ) ) )
        return None


def scrap_GB(ip_list_no_CIDR):
    repos = [ 'GenevaBuilder', 'GenevaBuilderDCEdge', 'GenevaBuilderDCNE' ]
    files = list ()
    for k in repos:
        allFiles = getListOfFiles ( home+"/"+k )
        allFiles = [ ele for ele in allFiles if ele not in erronus_files ]
        for a in allFiles:
            files.append ( a )
    logging.info (
        "Searching All filles in the following Repos .. 'GenevaBuilder','GenevaBuilderDCEdge','GenevaBuilderDCNE'" )
    for i in ip_list_no_CIDR:
        overall_matchedlines = list ()
        for j in files:
            scrap_every_file = SCRAP_repo_FILE ( repofiles=j, pattern=i )
            if scrap_every_file != [ ]:
                overall_matchedlines.append ( scrap_every_file )
                break
        if len ( overall_matchedlines ) != 0:
            logging.warning ( f"{i} FOUND AND CAN'T BE USED" )
        else:
            logging.info ( f"{i} NOT FOUND" )


def main():
    now_time = datetime.datetime.now ()
    setup_logging ( "INFO" )
    global args
    global home
    global erronus_files
    args = parse_args()
    home = str ( Path.home () )
    erronus_files = [
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca54-br-lbe-j1-r2/prefixlist-IPV6-DCA54-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca54-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt4-br-lbe-j1-r1/prefixlist-IPV6-PDT4-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt4-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt2-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt2-br-lbe-j1-r1/prefixlist-IPV6-PDT2-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca51-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca54-br-lbe-j1-r1/prefixlist-IPV6-DCA54-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca54-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt50-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt50-br-lbe-j1-r1/prefixlist-IPV6-PDT1-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt2-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt2-br-lbe-j1-r2/prefixlist-IPV6-PDT2-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt4-br-lbe-j1-r2/prefixlist-IPV6-PDT4-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt4-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt50-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/pdt50-br-lbe-j1-r2/prefixlist-IPV6-PDT1-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca50-br-lbe-j1-r2/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca50-br-lbe-j1-r2/prefixlist-IPV6-DCA50-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca51-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca51-br-lbe-j1-r1/prefixlist-IPV6-DCA51-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca50-br-lbe-j1-r1/dev-QFX3500.attr',
        f'{home}/GenevaBuilderDCEdge/deprecated-devices/dca50-br-lbe-j1-r1/prefixlist-IPV6-DCA50-JLB-VIPS.attr',
        f'{home}/GenevaBuilderDCNE/module/fPod/postprocessors/dump-targets-built_1',
        f'{home}/GenevaBuilderDCNE/build' ]

    logging.info ( "checking if GenevaBuilder Repo exist, it will be cloned if it doesn't exist in your home folder" )
    repo_creation ( reponame='GenevaBuilder' )

    logging.info ("checking if GenevaBuilderDCEdge Repo exist, it will be cloned if it doesn't exist in your home folder" )
    repo_creation ( reponame='GenevaBuilderDCEdge' )

    logging.info ("checking if GenevaBuilderDCNE Repo exist, it will be cloned if it doesn't exist in your home folder" )
    repo_creation ( reponame='GenevaBuilderDCNE' )

    ip_list_CIDR = args.ips.split ( ',' )
    ip_list_no_CIDR = list ()
    for i in ip_list_CIDR:
        ips_list = [ str ( ip ) for ip in ipaddress.IPv4Network ( i ) ]
        for j in ips_list:
            ip_list_no_CIDR.append ( j )
    scrap_GB ( ip_list_no_CIDR=ip_list_no_CIDR )
    ipv_bastions ( region=args.region, ips=args.ips )
    finish_time = datetime.datetime.now ()
    duration = finish_time-now_time
    minutes, seconds = divmod ( duration.seconds, 60 )
    print ( "" )
    print ( bcolors.UNDERLINE+"Script Time Stats:"+bcolors.ENDC )
    print (
        bcolors.WARNING
        +"The script took {} minutes and {} seconds to run.".format ( minutes, seconds )
        +bcolors.ENDC
    )


if __name__ == "__main__":
    main ()
