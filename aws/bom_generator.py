#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import argparse
import xlsxwriter
import logging
import re
import openpyxl
import sys
import json
import requests
import datetime
from collections import Counter, OrderedDict
from requests_kerberos import OPTIONAL, HTTPKerberosAuth
from bs4 import BeautifulSoup
from os.path import basename
import os
import yaml

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.portdata import portmodel
from dxd_tools_dev.portdata import border
from dxd_tools_dev.modules import nsm,mcm
from dxd_tools_dev.modules import mwinit_cookie
from dxd_tools_dev.bom import phoenix

datefmt = '%d-%b-%y %H:%M:%S'

##########################################################################
# Code for cutsheet upload to MCM
##########################################################################

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class MCMBaseException(Exception):
    pass

class UnknownMCM(MCMBaseException):
    pass

class MCM(object):
    def __init__(self, mcm_id, endpoint="https://mcm.amazon.com"):
        """Class to extract CSRF token and attach cutsheets to MCMs

        Args:
            mcm_id (str): ID of MCM that will need cutsheet attachment
            endpoint (str, optional): MCM URL - Defaults to "https://mcm.amazon.com".
        """
        self.endpoint = endpoint
        self.session = requests.Session()
        self.cookies = mwinit_cookie.get_midway_cookie_obj()
        self.kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
        self.friendly_id = mcm_id
        self._get_cm()
        self.session.headers.update(
            {"X-CSRF-Token": self.csrf_token, "Accept": "application/json"}
        )

    def _get_cm(self):
        url = self.endpoint + "/cms/" + self.friendly_id
        page = self.session.get(url, auth=self.kerberos_auth, cookies=self.cookies)
        soup = BeautifulSoup(page.text, "lxml")
        cm_uuid = soup.find(id="cm_uuid")
        status = soup.find(id="cm_status")
        if not cm_uuid:
            raise UnknownMCM('UUID not found for Friendly ID "%s"' % self.friendly_id)
        if not status:
            raise UnknownMCM(
                'MCM Status not found for Friendly ID "%s"' % self.friendly_id
            )
        self.uuid = cm_uuid
        self.status = status.get("value")
        self.csrf_token = soup.find("meta", attrs={"name": "csrf-token"}).get("content")
        if not self.uuid or not self.csrf_token:
            raise UnknownMCM('UUID not found for Friendly ID "%s"' % self.friendly_id)

    def get_cutsheet(self):
        url = (
            self.endpoint
            + "/attachments/get_attachments?parent_type=CM&parent_uuid="
            + self.uuid.get("value")
        )
        cutsheet_check = self.session.get(
            url, auth=self.kerberos_auth, cookies=self.cookies
        )
        output = json.loads(cutsheet_check.content.decode("utf8"))
        self.cutsheets = {
            l["file_name"]
            for l in sorted(output["attachments"], key=lambda x: x["last_updated_date"])
        }

    def upload(self, filename):
        url = self.endpoint + "/attachments/create_attachment"
        data = {"parent_type": "CM", "parent_uuid": self.uuid.get("value")}
        with open(filename, "rb") as fh:
            files = [("files[]", (basename(filename), fh))]
            response = self.session.post(url, data=data, files=files)

        response.raise_for_status()
        res = response.json()

        if "err_msg" in res:
            raise MCMBaseException(res["err_msg"])

        return res

def cookie_verify(func_to_decorate: str):
    """Decorator that verifies if HTTP cookie is valid

    Args:
        func_to_decorate (str): MCM creation function
    """

    def new_func(*original_args):
        print()
        print(
            "   Testing HTTP Cookie validity (below you will see HTTP cookie debug info)"
        )
        cookies = mwinit_cookie.get_midway_cookie_obj()
        if len(cookies) >= 9:
            return func_to_decorate(*original_args)
        else:
            print(
                f"   One (or more) issues found with {bcolors.FAIL}HTTP cookies{bcolors.ENDC}"
            )

    return new_func

@cookie_verify
def create_mcm(site,build_type):
    try:
        mcm_create = mcm.mcm_creation('bom',site,build_type)
    except Exception as error:
        logging.error('MCM could not be created {}'.format(error))

    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = "https://mcm.amazon.com/cms/" + mcm_id

    logging.info('{} successfully created'.format(mcm_link))

    mcm_steps = [
        {
            "title": "Review BOM",
            "time": 10,
            "description": "Review attached BOM",
            "rollback": "NA",
        }
    ]

    try:
        mcm.mcm_update(mcm_id, mcm_uid, mcm_overview, mcm_steps)
        return mcm_id
    except Exception as error:
        logging.error('{} could not be updated {}'.format(mcm_id,error))

def create_mcm_no_attach(site,build_type):
    try:
        mcm_create = mcm.mcm_creation('bom',site,build_type)
    except Exception as error:
        logging.error('MCM could not be created {}'.format(error))

    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = "https://mcm.amazon.com/cms/" + mcm_id

    print('{} - MCM {} successfully created'.format(datetime.datetime.utcnow().strftime(datefmt),mcm_link))

    mcm_steps = [
        {
            "title": "Review BOM",
            "time": 10,
            "description": "Review BOM",
            "rollback": "NA",
        }
    ]

    try:
        mcm.mcm_update(mcm_id, mcm_uid, mcm_overview, mcm_steps)
        return mcm_id
    except Exception as error:
        logging.error('{} could not be updated {}'.format(mcm_id,error))

##########################################################################
# Code for generating BOM
##########################################################################

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='bom_generator.py', description='DX BOM generation Script')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')
    phoenix_regular_parser = subparsers.add_parser('phoenix_regular', help='BOM for Phoenix in DX regular POP')
    phoenix_regular_parser.add_argument("-st", "--site", action="store", dest="site", required=True, help="Specify Site for Phoenix BOM")
    phoenix_regular_parser.add_argument("-phx_o", "--phoenix_optic", action="store", dest="phoenix_optic", required=True, help="Optic for connecting Phoenix to vc-cor/br-tra")
    phoenix_regular_parser.add_argument("-cor", "--vccor", default=False, action='store_true', dest="vccor", help="Specify -cor if want to include vc-cor in BOM. vc-cor will not be included by default")
    phoenix_regular_parser.add_argument("-cor_o", "--vccor_optic", action="store", dest="vccor_optic", help="Optic for connecting vc-cor to br-kct")
    phoenix_regular_parser.add_argument("-bmn", "--border_management_network", default=False, action='store_true', dest="border_management_network", help="Specify -bmn if want to include BMN in BOM. BMN will not be included by default")
    phoenix_regular_parser.add_argument("-lc_1g", "--linecard_40x1g",action="store", dest="linecard_40x1g", help="Specify number of 1G linecard MPCE Type 2 3D")
    phoenix_regular_parser.add_argument("-lc_32x10g", "--linecard_32x10g",action="store", dest="linecard_32x10g",help="Specify number of 32x10G linecard MPC4E 3D 32XGE")
    phoenix_regular_parser.add_argument("-lc_16x10g", "--linecard_16x10g",action="store", dest="linecard_16x10g",help="Specify number of 16x10G linecard MPC 3D 16x 10GE")
    phoenix_regular_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach bom. BOM will be attached to MCM by default (if -no_att is not specified)")

    phoenix_small_parser = subparsers.add_parser('phoenix_dx_small', help='BOM for Phoenix in DX Small/Pioneer regular POP')
    phoenix_small_parser.add_argument("-st", "--site", action="store", dest="site", required=True, help="Specify Site for Phoenix BOM")
    phoenix_small_parser.add_argument("-cor_p1", "--vccor_p1", default=False, action='store_true', dest="vccor_p1", help="Specify -cor_p1 if want to include vc-cor for Border parent P1 in BOM. vc-cor will not be included by default")
    phoenix_small_parser.add_argument("-cor_p1_o", "--vccor_p1_optic", action="store", dest="vccor_p1_optic", help="Optic for connecting vc-cor in Border parent P1 to br-kct")
    phoenix_small_parser.add_argument("-cor_p2", "--vccor_p2", default=False, action='store_true', dest="vccor_p2", help="Specify -cor_p2 if want to include vc-cor for Border parent P2 in BOM. vc-cor will not be included by default")
    phoenix_small_parser.add_argument("-cor_p2_o", "--vccor_p2_optic", action="store", dest="vccor_p2_optic", help="Optic for connecting vc-cor in Border parent P2 to br-kct")
    phoenix_small_parser.add_argument("-dar", "--vcdar", default=False, action='store_true', dest="vcdar", help="Specify -dar if want to include vc-dar in BOM. vc-dar will not be included by default")
    phoenix_small_parser.add_argument("-dar_o", "--vcdar_optic", action="store", dest="vcdar_optic", help="Optic for connecting vc-dar to vc-cor/br-tra")
    phoenix_small_parser.add_argument("-bmn", "--border_management_network", default=False, action='store_true', dest="border_management_network", help="Specify -bmn if want to include BMN in BOM. BMN will not be included by default")
    phoenix_small_parser.add_argument("-lc_1g", "--linecard_40x1g",action="store", dest="linecard_40x1g", help="Specify number of 1G linecard MPCE Type 2 3D")
    phoenix_small_parser.add_argument("-lc_32x10g", "--linecard_32x10g",action="store", dest="linecard_32x10g",help="Specify number of 32x10G linecard MPC4E 3D 32XGE")
    phoenix_small_parser.add_argument("-lc_16x10g", "--linecard_16x10g",action="store", dest="linecard_16x10g",help="Specify number of 16x10G linecard MPC 3D 16x 10GE")
    phoenix_small_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach bom. BOM will be attached to MCM by default (if -no_att is not specified)")

    return main_parser.parse_args()

def main():
    cli_arguments = parse_args()
    if cli_arguments.command == 'phoenix_regular':
        site = cli_arguments.site
        phx_o = cli_arguments.phoenix_optic
        vccor = cli_arguments.vccor
        vccor_o = cli_arguments.vccor_optic
        bmn = cli_arguments.border_management_network
        lc_40x1g = cli_arguments.linecard_40x1g
        lc_32x10g = cli_arguments.linecard_32x10g
        lc_16x10g = cli_arguments.linecard_16x10g

        phoenix.create_phoenix_regular_bom(site,phx_o,vccor,vccor_o,bmn,lc_40x1g,lc_32x10g,lc_16x10g)

        build_type = 'Phoenix'

        if cli_arguments.no_attachment:
            mcm_info = create_mcm(site,build_type)
            logging.info('Uploading BOM to {}'.format(mcm_info))
            bom_file = MCM(mcm_info)
            bom_file.upload('/var/tmp/{}_Phoenix_BOM_v1.xlsx'.format(site.upper()))
            logging.info('BOM uploaded to {}'.format(mcm_info))
            os.remove('/var/tmp/{}_Phoenix_BOM_v1.xlsx'.format(site.upper()))

        else:
            mcm_info = create_mcm_no_attach(site,build_type)
            print("{} - BOM created /var/tmp/{}_Phoenix_BOM_v1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))

    elif cli_arguments.command == 'phoenix_dx_small':
        site = cli_arguments.site
        vccor_p1 = cli_arguments.vccor_p1
        vccor_p1_o = cli_arguments.vccor_p1_optic
        vccor_p2 = cli_arguments.vccor_p2
        vccor_p2_o = cli_arguments.vccor_p2_optic
        dar = cli_arguments.vcdar
        dar_o = cli_arguments.vcdar_optic
        bmn = cli_arguments.border_management_network
        lc_40x1g = cli_arguments.linecard_40x1g
        lc_32x10g = cli_arguments.linecard_32x10g
        lc_16x10g = cli_arguments.linecard_16x10g

        phoenix.create_phoenix_dx_small_bom(site,vccor_p1,vccor_p1_o,vccor_p2,vccor_p2_o,dar,dar_o,bmn,lc_40x1g,lc_32x10g,lc_16x10g)

        build_type = 'Phoenix'

        if cli_arguments.no_attachment:
            mcm_info = create_mcm(site,build_type)
            logging.info('Uploading BOM to {}'.format(mcm_info))
            bom_file = MCM(mcm_info)
            bom_file.upload('/var/tmp/{}_Phoenix_BOM_v1.xlsx'.format(site.upper()))
            logging.info('BOM uploaded to {}'.format(mcm_info))
            os.remove('/var/tmp/{}_Phoenix_BOM_v1.xlsx'.format(site.upper()))

        else:
            mcm_info = create_mcm_no_attach(site,build_type)
            print("{} - BOM created /var/tmp/{}_Phoenix_BOM_v1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),site.upper()))

if __name__ == '__main__':
     main()
