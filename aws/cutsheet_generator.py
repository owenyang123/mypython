#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import argparse
import logging
import re
import sys
import openpyxl
import json
import requests
import datetime
from collections import Counter, OrderedDict
from requests_kerberos import OPTIONAL, HTTPKerberosAuth
from bs4 import BeautifulSoup
from os.path import basename
import os

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

from dxd_tools_dev.datastore import ddb
from dxd_tools_dev.portdata import portmodel
from dxd_tools_dev.portdata import border
from isd_tools_dev.modules import nsm as nsm_isd
from dxd_tools_dev.modules import nsm as nsm_dxd
from dxd_tools_dev.modules import mcm
from dxd_tools_dev.modules import mwinit_cookie
from dxd_tools_dev.modules import jukebox
from dxd_tools_dev.cutsheet import cutsheet_operations, centennial, phoenix

capacity = {'small_car_pair':80,'medium_car_pair':275,'large_car_pair':550}
capacity_phoenix = {'small':160,'medium':320,'large':640}
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


##########################################################################
# Code for generating cutsheets
##########################################################################

def parse_args(fake_args=None):
    main_parser = argparse.ArgumentParser(prog='cutsheet_generator.py', description='DX Cutsheet generation Script')
    subparsers = main_parser.add_subparsers(help='commands', dest='command')
    standard_centennial_parser = subparsers.add_parser('standard_centennial', help='Cutsheet for Standard Centennial')
    standard_centennial_parser.add_argument("-car", "--vc_car_prefix", action="store", dest="vc_car_prefix", required=True, help="Centennial vc-car prefix without router name e.g sea73-vc-car-pdx-p2")
    standard_centennial_parser.add_argument("-cor", "--vc_cor_brick", action="store", dest="vc_cor_brick", required=True, help="vc-cor Brick name for Centennial e.g sea4-vc-cor-b2")
    standard_centennial_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach cutsheet. Cutsheet will be attached to MCM by default (if -no_att is not specified)")

    standard_phoenix_renaissance_parser = subparsers.add_parser('standard_phoenix_renaissance', help='Cutsheet for Standard Phoenix Renaissance')
    standard_phoenix_renaissance_parser.add_argument("-car", "--vc_car_prefix", action="store", dest="vc_car_prefix", required=True, help="vc-car prefix without router name e.g sea73-vc-car-pdx-p2")
    standard_phoenix_renaissance_parser.add_argument("-cor", "--vc_cor_brick", action="store", dest="vc_cor_brick", help="vc-cor Brick name e.g sea4-vc-cor-b2")
    standard_phoenix_renaissance_parser.add_argument("-site", "--border_site", action="store", dest="border_site", help="Site for br-tra and br-kct e.g iad2")
    standard_phoenix_renaissance_parser.add_argument("-size", "--pop_size", action="store", dest="pop_size", required=True, help="Size of POP e.g small/medium/large")
    standard_phoenix_renaissance_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach cutsheet. Cutsheet will be attached to MCM by default (if -no_att is not specified)")

    standard_small_centennial_parser = subparsers.add_parser('standard_small_pop_centennial', help='Cutsheet for Standard Small POP Centennial')
    standard_small_centennial_parser.add_argument("-car", "--vc_car_prefix", action="store", dest="vc_car_prefix", required=True, help="Centennial vc-car prefix without router name e.g sea73-vc-car-pdx-p2")
    standard_small_centennial_parser.add_argument("-cor_p1", "--vc_cor_brick_parent_1", action="store", dest="vc_cor_brick_parent_1", required=True, help="vc-cor Brick name of Border parent 1 e.g dub2-vc-cor-b1")
    standard_small_centennial_parser.add_argument("-cor_p2", "--vc_cor_brick_parent_2", action="store", dest="vc_cor_brick_parent_2", required=True, help="vc-cor Brick name of Border parent 2 e.g dub3-vc-cor-b1")
    standard_small_centennial_parser.add_argument("-dar", "--vc_dar_routers", action="store", dest="vc_dar_routers", required=True, help="Comma separated vc-dar routers e.g dub65-vc-dar-r1,dub65-vc-dar-r2,dub65-vc-dar-r3,dub65-vc-dar-r4")
    standard_small_centennial_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach cutsheet. Cutsheet will be attached to MCM by default (if -no_att is not specified)")

    standard_small_phoenix_renaissance_parser = subparsers.add_parser('standard_small_pop_phoenix_renaissance', help='Cutsheet for Standard Small POP Centennial')
    standard_small_phoenix_renaissance_parser.add_argument("-car", "--vc_car_prefix", action="store", dest="vc_car_prefix", required=True, help="Centennial vc-car prefix without router name e.g sea73-vc-car-pdx-p2")
    standard_small_phoenix_renaissance_parser.add_argument("-cor_p1", "--vc_cor_brick_parent_1", action="store", dest="vc_cor_brick_parent_1", help="vc-cor Brick name of Border parent 1 e.g dub2-vc-cor-b1")
    standard_small_phoenix_renaissance_parser.add_argument("-cor_p2", "--vc_cor_brick_parent_2", action="store", dest="vc_cor_brick_parent_2", help="vc-cor Brick name of Border parent 2 e.g dub3-vc-cor-b1")
    standard_small_phoenix_renaissance_parser.add_argument("-dar", "--vc_dar_routers", action="store", dest="vc_dar_routers", required=True, help="Comma separated vc-dar routers e.g dub65-vc-dar-r1,dub65-vc-dar-r2,dub65-vc-dar-r3,dub65-vc-dar-r4")
    standard_small_phoenix_renaissance_parser.add_argument("-site_p1", "--border_site_p1", action="store", dest="border_site_p1", help="Site for br-tra and br-kct e.g iad2")
    standard_small_phoenix_renaissance_parser.add_argument("-site_p2", "--border_site_p2", action="store", dest="border_site_p2", help="Site for br-tra and br-kct e.g iad4")
    standard_small_phoenix_renaissance_parser.add_argument("-size", "--pop_size", action="store", dest="pop_size", required=True, help="Size of POP e.g small/medium/large")
    standard_small_phoenix_renaissance_parser.add_argument("-no_att", "--no_attachment", default=True, action='store_false', dest="no_attachment", help="Specify -no_att flag to not attach cutsheet. Cutsheet will be attached to MCM by default (if -no_att is not specified)")

    return main_parser.parse_args()

@cookie_verify
def create_mcm(site,mcm_devices,build_type):
    try:
        mcm_create = mcm.mcm_creation('mcm_title_overview_cutsheet_newbuild',site,mcm_devices,build_type)
    except Exception as error:
        logging.error('MCM could not be created {}'.format(error))

    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = "https://mcm.amazon.com/cms/" + mcm_id

    logging.info('{} successfully created'.format(mcm_link))

    mcm_steps = [
        {
            "title": "Review Cutsheet",
            "time": 10,
            "description": "Review attached cutsheet",
            "rollback": "NA",
        }
    ]

    try:
        mcm.mcm_update(mcm_id, mcm_uid, mcm_overview, mcm_steps)
        return mcm_id
    except Exception as error:
        logging.error('{} could not be updated {}'.format(mcm_id,error))

def create_mcm_no_attach(site,mcm_devices,build_type):
    try:
        mcm_create = mcm.mcm_creation('mcm_title_overview_cutsheet_newbuild',site,mcm_devices,build_type)
    except Exception as error:
        logging.error('MCM could not be created {}'.format(error))

    mcm_id = mcm_create[0]
    mcm_overview = mcm_create[2]
    mcm_uid = mcm_create[1]
    mcm_link = "https://mcm.amazon.com/cms/" + mcm_id

    print('{} - MCM {} successfully created'.format(datetime.datetime.utcnow().strftime(datefmt),mcm_link))

    mcm_steps = [
        {
            "title": "Review Cutsheet",
            "time": 10,
            "description": "Review cutsheet",
            "rollback": "NA",
        }
    ]

    try:
        mcm.mcm_update(mcm_id, mcm_uid, mcm_overview, mcm_steps)
        return mcm_id
    except Exception as error:
        logging.error('{} could not be updated {}'.format(mcm_id,error))

def main():
    cli_arguments = parse_args()
    if cli_arguments.command == 'standard_centennial':
        if cutsheet_operations.validate_standard_centennial_input(cli_arguments.vc_car_prefix,cli_arguments.vc_cor_brick):
            vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v5'
            vc_cor_brick_worksheet = cli_arguments.vc_cor_brick
            br_kct_worksheet = vc_cor_brick_worksheet.split('-')[0] + '-br-kct-p1'
            vc_cas = vc_car_prefix_worksheet.split('-')
            vc_cas[2] = 'cas'
            vc_cas_prefix_worksheet = '-'.join(vc_cas)
            site = vc_car_prefix_worksheet.split('-')[0].lower()
            vccor_site = cli_arguments.vc_cor_brick.split('-')[0].lower()
            cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
        vc_cor_list = cutsheet_operations.check_device_exists(vc_cor_brick_worksheet)

        mcm_devices,cutsheet_name,build_type = centennial.create_centennial_regular_cutsheet(vc_car_prefix_worksheet,vc_cor_brick_worksheet,br_kct_worksheet,vc_cas_prefix_worksheet,vc_cor_list,site,vccor_site)

        logging.info('Creating Cutsheet MCM')

        if cli_arguments.no_attachment:
            mcm_info = create_mcm(site,mcm_devices,build_type)
            logging.info('Uploading cutsheet to {}'.format(mcm_info))
            cutsheet_file = MCM(mcm_info)
            cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
            logging.info('Cutsheet uploaded to {}'.format(mcm_info))
            os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

        else:
            mcm_info = create_mcm_no_attach(site,mcm_devices,build_type)
            print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

    elif cli_arguments.command == 'standard_phoenix_renaissance':
        if cli_arguments.vc_car_prefix and cli_arguments.border_site and cli_arguments.pop_size and cli_arguments.vc_cor_brick:
            logging.error('Invalid input. Pass either -cor/--vc_cor_brick (to use vc-cor) or -site/--border_site (to use br-tra) as arguments. Exiting')
            sys.exit()

        elif cli_arguments.vc_car_prefix and cli_arguments.border_site and cli_arguments.pop_size:
            if cutsheet_operations.validate_car_input(cli_arguments.vc_car_prefix) and cutsheet_operations.validate_border_site_input(cli_arguments.border_site.lower()):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                site = cli_arguments.border_site.lower()
                br_kct_worksheet = site + '-br-kct-p1'
                br_tra_prefix = site + '-br-tra'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)

                br_tra_list = cutsheet_operations.check_device_exists(br_tra_prefix)

                mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_regular_tra_cutsheet(vc_car_prefix_worksheet,br_kct_worksheet,br_tra_prefix,br_tra_list,vc_cas_prefix_worksheet,site,dx_site,pop_size,region,rack)

                logging.info('Creating Cutsheet MCM')

                if cli_arguments.no_attachment:
                    mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                    logging.info('Uploading cutsheet to {}'.format(mcm_info))
                    cutsheet_file = MCM(mcm_info)
                    cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                    logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                    os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

                else:
                    mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                    print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

        elif cli_arguments.vc_car_prefix and cli_arguments.vc_cor_brick and cli_arguments.pop_size:
            if cutsheet_operations.validate_standard_centennial_input(cli_arguments.vc_car_prefix,cli_arguments.vc_cor_brick):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                vc_cor_brick_worksheet = cli_arguments.vc_cor_brick
                site = cli_arguments.vc_cor_brick.split('-')[0].lower()
                br_kct_worksheet = site + '-br-kct-p1'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                vc_cor_brick_number = vc_cor_brick_worksheet.split('-')[3].strip('b')
            vc_cor_list = cutsheet_operations.check_device_exists(vc_cor_brick_worksheet)

            mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_regular_vccor_cutsheet(vc_car_prefix_worksheet,vc_cor_brick_worksheet,vc_cor_brick_number,vc_cor_list,br_kct_worksheet,vc_cas_prefix_worksheet,site,dx_site,pop_size,region,rack)

            logging.info('Creating Cutsheet MCM')

            if cli_arguments.no_attachment:
                mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                logging.info('Uploading cutsheet to {}'.format(mcm_info))
                cutsheet_file = MCM(mcm_info)
                cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

            else:
                mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

    elif cli_arguments.command == 'standard_small_pop_centennial':
        if cutsheet_operations.validate_standard_small_pop_centennial_input(cli_arguments.vc_car_prefix,cli_arguments.vc_cor_brick_parent_1,cli_arguments.vc_cor_brick_parent_2,cli_arguments.vc_dar_routers):
            vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v5'
            vc_cor_brick_p1_worksheet = cli_arguments.vc_cor_brick_parent_1
            vc_cor_brick_p2_worksheet = cli_arguments.vc_cor_brick_parent_2
            br_kct_p1_worksheet = cli_arguments.vc_cor_brick_parent_1.split('-')[0] + '-br-kct-p1'
            br_kct_p2_worksheet = cli_arguments.vc_cor_brick_parent_2.split('-')[0] + '-br-kct-p1'
            vc_cas = vc_car_prefix_worksheet.split('-')
            vc_cas[2] = 'cas'
            vc_cas_prefix_worksheet = '-'.join(vc_cas)
            site = vc_car_prefix_worksheet.split('-')[0].lower()
            vccor_p1_site = cli_arguments.vc_cor_brick_parent_1.split('-')[0].lower()
            vccor_p2_site = cli_arguments.vc_cor_brick_parent_2.split('-')[0].lower()
            vc_dar_routers = cli_arguments.vc_dar_routers.split(',')
            vc_dar = cli_arguments.vc_dar_routers.split(',')[0].split('-')
            vc_dar.pop()
            vc_dar_worksheet = '-'.join(vc_dar)
            cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
        vc_cor_p1_list = cutsheet_operations.check_device_exists(vc_cor_brick_p1_worksheet)
        vc_cor_p2_list = cutsheet_operations.check_device_exists(vc_cor_brick_p2_worksheet)
        vc_dar_list = cutsheet_operations.check_device_exists(cli_arguments.vc_dar_routers)

        mcm_devices,cutsheet_name,build_type = centennial.create_centennial_small_cutsheet(vc_car_prefix_worksheet,vc_cor_brick_p1_worksheet,vc_cor_brick_p2_worksheet,br_kct_p1_worksheet,br_kct_p2_worksheet,vc_cas_prefix_worksheet,site,vccor_p1_site,vccor_p2_site,vc_dar_routers,vc_dar_worksheet,vc_cor_p1_list,vc_cor_p2_list,vc_dar_list)

        logging.info('Creating Cutsheet MCM')

        if cli_arguments.no_attachment:
            mcm_info = create_mcm(site,mcm_devices,build_type)
            logging.info('Uploading cutsheet to {}'.format(mcm_info))
            cutsheet_file = MCM(mcm_info)
            cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
            logging.info('Cutsheet uploaded to {}'.format(mcm_info))
            os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

        else:
            mcm_info = create_mcm_no_attach(site,mcm_devices,build_type)
            print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

    elif cli_arguments.command == 'standard_small_pop_phoenix_renaissance':
        if cli_arguments.vc_car_prefix and cli_arguments.border_site_p1 and cli_arguments.border_site_p2 and cli_arguments.vc_dar_routers and cli_arguments.pop_size:
            if cutsheet_operations.validate_car_input(cli_arguments.vc_car_prefix) and cutsheet_operations.validate_border_site_input(cli_arguments.border_site_p1.lower()) and cutsheet_operations.validate_border_site_input(cli_arguments.border_site_p2.lower()) and cutsheet_operations.validate_dar_input(cli_arguments.vc_dar_routers):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                site_p1 = cli_arguments.border_site_p1.lower()
                site_p2 = cli_arguments.border_site_p2.lower()
                br_tra_p1_prefix = site_p1 + '-br-tra'
                br_tra_p2_prefix = site_p2 + '-br-tra'
                vc_cor_p1_prefix = site_p1 + '-vc-cor-b'
                vc_cor_p2_prefix = site_p2 + '-vc-cor-b'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                vc_dar_routers = cli_arguments.vc_dar_routers.split(',')
                vc_dar = cli_arguments.vc_dar_routers.split(',')[0].split('-')
                vc_dar.pop()
                vc_dar_worksheet = '-'.join(vc_dar)
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                vc_dar_list = cutsheet_operations.check_device_exists(cli_arguments.vc_dar_routers)
                vc_car = cli_arguments.vc_car_prefix.split('-')
                vc_car.pop()
                vc_car.pop()
                vc_car_regex = '-'.join(vc_car)
                cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
                vc_car_list = cutsheet_operations.check_device_exists(vc_car_regex)
                br_tra_p1_list = cutsheet_operations.check_device_exists(br_tra_p1_prefix)
                br_tra_p2_list = cutsheet_operations.check_device_exists(br_tra_p2_prefix)
                cent_car_list = [car for car in vc_car_list if re.match('.*-v(2|5)-.*',car)]

                mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_small_tra_cutsheet(vc_car_prefix_worksheet,br_tra_p1_prefix,br_tra_p2_prefix,vc_cor_p1_prefix,vc_cor_p2_prefix,vc_cas_prefix_worksheet,vc_dar_routers,vc_dar_worksheet,vc_dar_list,vc_car_list,br_tra_p1_list,br_tra_p2_list,cent_car_list,site_p1,site_p2,dx_site,region,rack,pop_size)

                logging.info('Creating Cutsheet MCM')

                if cli_arguments.no_attachment:
                    mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                    logging.info('Uploading cutsheet to {}'.format(mcm_info))
                    cutsheet_file = MCM(mcm_info)
                    cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                    logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                    os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

                else:
                    mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                    print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

        elif cli_arguments.vc_car_prefix and cli_arguments.vc_cor_brick_parent_1 and cli_arguments.vc_cor_brick_parent_2 and cli_arguments.vc_dar_routers and cli_arguments.pop_size:
            if cutsheet_operations.validate_standard_small_pop_centennial_input(cli_arguments.vc_car_prefix,cli_arguments.vc_cor_brick_parent_1,cli_arguments.vc_cor_brick_parent_2,cli_arguments.vc_dar_routers):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                vc_cor_brick_p1_worksheet = cli_arguments.vc_cor_brick_parent_1
                vc_cor_brick_p2_worksheet = cli_arguments.vc_cor_brick_parent_2
                vccor_p1_site = cli_arguments.vc_cor_brick_parent_1.split('-')[0].lower()
                vccor_p2_site = cli_arguments.vc_cor_brick_parent_2.split('-')[0].lower()
                br_kct_p1_worksheet = vccor_p1_site + '-br-kct-p1'
                br_kct_p2_worksheet = vccor_p2_site + '-br-kct-p1'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                vc_dar_routers = cli_arguments.vc_dar_routers.split(',')
                vc_dar = cli_arguments.vc_dar_routers.split(',')[0].split('-')
                vc_dar.pop()
                vc_dar_worksheet = '-'.join(vc_dar)
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                vc_dar_list = cutsheet_operations.check_device_exists(cli_arguments.vc_dar_routers)
                vc_car = cli_arguments.vc_car_prefix.split('-')
                vc_car.pop()
                vc_car.pop()
                vc_car_regex = '-'.join(vc_car)
                cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
                vc_car_list = cutsheet_operations.check_device_exists(vc_car_regex)
                cent_car_list = [car for car in vc_car_list if re.match('.*-v(2|5)-.*',car)]
                vc_cor_p1_list = cutsheet_operations.check_device_exists(vc_cor_brick_p1_worksheet)
                vc_cor_p2_list = cutsheet_operations.check_device_exists(vc_cor_brick_p2_worksheet)
                vc_cor_brick_p1 = vc_cor_brick_p1_worksheet.split('-')[3].strip('b')
                vc_cor_brick_p2 = vc_cor_brick_p2_worksheet.split('-')[3].strip('b')

                mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_small_vccor_cutsheet(vc_car_prefix_worksheet,vc_cor_brick_p1_worksheet,vc_cor_brick_p2_worksheet,br_kct_p1_worksheet,br_kct_p2_worksheet,vc_cor_p1_list,vc_cor_p2_list,vc_cor_brick_p1,vc_cor_brick_p2,vc_cas_prefix_worksheet,vc_dar_routers,vc_dar_worksheet,vc_dar_list,vc_car_list,cent_car_list,vccor_p1_site,vccor_p2_site,dx_site,region,rack,pop_size)

                logging.info('Creating Cutsheet MCM')

                if cli_arguments.no_attachment:
                    mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                    logging.info('Uploading cutsheet to {}'.format(mcm_info))
                    cutsheet_file = MCM(mcm_info)
                    cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                    logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                    os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

                else:
                    mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                    print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

        elif cli_arguments.vc_car_prefix and cli_arguments.border_site_p1 and cli_arguments.vc_cor_brick_parent_2 and cli_arguments.vc_dar_routers and cli_arguments. pop_size:
            if cutsheet_operations.validate_car_input(cli_arguments.vc_car_prefix) and cutsheet_operations.validate_border_site_input(cli_arguments.border_site_p1.lower()) and cutsheet_operations.validate_cor_input(cli_arguments.vc_cor_brick_parent_2.lower()) and cutsheet_operations.validate_dar_input(cli_arguments.vc_dar_routers):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                site_p1 = cli_arguments.border_site_p1.lower()
                br_tra_prefix = site_p1 + '-br-tra'
                vc_cor_brick_worksheet = cli_arguments.vc_cor_brick_parent_2
                vccor_site = cli_arguments.vc_cor_brick_parent_2.split('-')[0].lower()
                br_kct_worksheet = vccor_site + '-br-kct-p1'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                vc_dar_routers = cli_arguments.vc_dar_routers.split(',')
                vc_dar = cli_arguments.vc_dar_routers.split(',')[0].split('-')
                vc_dar.pop()
                vc_dar_worksheet = '-'.join(vc_dar)
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                vc_dar_list = cutsheet_operations.check_device_exists(cli_arguments.vc_dar_routers)
                vc_car = cli_arguments.vc_car_prefix.split('-')
                vc_car.pop()
                vc_car.pop()
                vc_car_regex = '-'.join(vc_car)
                cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
                vc_car_list = cutsheet_operations.check_device_exists(vc_car_regex)
                cent_car_list = [car for car in vc_car_list if re.match('.*-v(2|5)-.*',car)]
                vc_cor_list = cutsheet_operations.check_device_exists(vc_cor_brick_worksheet)
                vc_cor_brick = vc_cor_brick_worksheet.split('-')[3].strip('b')
                br_tra_list = cutsheet_operations.check_device_exists(br_tra_prefix)

                mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_small_tra_cor_cutsheet(site_p1,vc_car_prefix_worksheet,br_tra_prefix,br_tra_list,vc_cor_brick_worksheet,br_kct_worksheet,vc_cor_list,vc_cor_brick,vc_cas_prefix_worksheet,vc_dar_routers,vc_dar_worksheet,vc_dar_list,vc_car_list,cent_car_list,vccor_site,dx_site,region,rack,pop_size)

                logging.info('Creating Cutsheet MCM')

                if cli_arguments.no_attachment:
                    mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                    logging.info('Uploading cutsheet to {}'.format(mcm_info))
                    cutsheet_file = MCM(mcm_info)
                    cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                    logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                    os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

                else:
                    mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                    print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

        elif cli_arguments.vc_car_prefix and cli_arguments.border_site_p2 and cli_arguments.vc_cor_brick_parent_1 and cli_arguments.vc_dar_routers and cli_arguments. pop_size:
            if cutsheet_operations.validate_car_input(cli_arguments.vc_car_prefix) and cutsheet_operations.validate_border_site_input(cli_arguments.border_site_p2.lower()) and cutsheet_operations.validate_cor_input(cli_arguments.vc_cor_brick_parent_1.lower()) and cutsheet_operations.validate_dar_input(cli_arguments.vc_dar_routers):
                vc_car_prefix_worksheet = cli_arguments.vc_car_prefix + '-v4'
                site_p2 = cli_arguments.border_site_p2.lower()
                br_tra_prefix = site_p2 + '-br-tra'
                vc_cor_brick_worksheet = cli_arguments.vc_cor_brick_parent_1
                vccor_site = cli_arguments.vc_cor_brick_parent_1.split('-')[0].lower()
                br_kct_worksheet = vccor_site + '-br-kct-p1'
                vc_cas = vc_car_prefix_worksheet.split('-')
                vc_cas[2] = 'cas'
                vc_cas_prefix_worksheet = '-'.join(vc_cas)
                dx_site = vc_car_prefix_worksheet.split('-')[0].lower()
                vc_dar_routers = cli_arguments.vc_dar_routers.split(',')
                vc_dar = cli_arguments.vc_dar_routers.split(',')[0].split('-')
                vc_dar.pop()
                vc_dar_worksheet = '-'.join(vc_dar)
                region = vc_car_prefix_worksheet.split('-')[3].lower()
                rack = vc_car_prefix_worksheet.split('-')[4].strip('p')
                pop_size = cli_arguments.pop_size.lower()
                vc_dar_list = cutsheet_operations.check_device_exists(cli_arguments.vc_dar_routers)
                vc_car = cli_arguments.vc_car_prefix.split('-')
                vc_car.pop()
                vc_car.pop()
                vc_car_regex = '-'.join(vc_car)
                cutsheet_operations.verify_vc_car(vc_car_prefix_worksheet)
                vc_car_list = cutsheet_operations.check_device_exists(vc_car_regex)
                cent_car_list = [car for car in vc_car_list if re.match('.*-v(2|5)-.*',car)]
                vc_cor_list = cutsheet_operations.check_device_exists(vc_cor_brick_worksheet)
                vc_cor_brick = vc_cor_brick_worksheet.split('-')[3].strip('b')
                br_tra_list = cutsheet_operations.check_device_exists(br_tra_prefix)

                mcm_devices,cutsheet_name,build_type = phoenix.create_phoenix_small_tra_cor_cutsheet(site_p2,vc_car_prefix_worksheet,br_tra_prefix,br_tra_list,vc_cor_brick_worksheet,br_kct_worksheet,vc_cor_list,vc_cor_brick,vc_cas_prefix_worksheet,vc_dar_routers,vc_dar_worksheet,vc_dar_list,vc_car_list,cent_car_list,vccor_site,dx_site,region,rack,pop_size)

                logging.info('Creating Cutsheet MCM')

                if cli_arguments.no_attachment:
                    mcm_info = create_mcm(dx_site,mcm_devices,build_type)
                    logging.info('Uploading cutsheet to {}'.format(mcm_info))
                    cutsheet_file = MCM(mcm_info)
                    cutsheet_file.upload("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))
                    logging.info('Cutsheet uploaded to {}'.format(mcm_info))
                    os.remove("/var/tmp/{}_cutsheetV1.xlsx".format(cutsheet_name))

                else:
                    mcm_info = create_mcm_no_attach(dx_site,mcm_devices,build_type)
                    print("{} - cutsheet created /var/tmp/{}_cutsheetV1.xlsx".format(datetime.datetime.utcnow().strftime(datefmt),cutsheet_name))

if __name__ == '__main__':
     main()
