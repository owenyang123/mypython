#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

import subprocess
import socket
import datetime
import sys
import re
import os
import time
from subprocess import Popen, PIPE, STDOUT

from dxd_tools_dev.modules import simissue, mcm
from dxd_tools_dev.site_assessment import dxbi_data
from dxd_tools_dev.datastore import ddb

datefmt = '%d-%b-%y %H:%M:%S'
site_assessment_table = 'auto_dx_site_assessor_table'
ddb_material_set = 'com.amazon.credentials.isengard.749865518066.user/dx_tools_ddb_rw'
aws_region = 'us-east-2'

first_msg = 'This is an automated site assessment run.\nMore information on automated site \
assessment can be found in https://w.amazon.com/bin/view/Interconnect/Tools/DirectConnectSiteAssessment\n\n'

last_msg = '\n\nTo create cutsheet, use CutsheetGenerator https://w.amazon.com/bin/view/Interconnect/Tools/CutsheetGenerator\n\n\
To create BOM, use Phoenix HLD https://w.amazon.com/bin/view/AWSDirectConnect/Phoenix/HLD/#HPhoenixSKUOptions\n\
If you are using Border devices, make sure you include optics for them'

def main():
    issue = simissue.SimIssue()
    issue = simissue.SimIssue(odin_set='com.amazon.credentials.isengard.749865518066.user/dxdeploymenttools_SIM_update')
    
    site_assessment_records = list()
    hostname = socket.gethostname()

    if '-'.join(hostname.split('-')[:2]) != 'aws-dxtools':
        print('{} - Script cannot be executed on {}. It must be executed on AWS-DXTOOLS hostclass. Exiting'.format(datetime.datetime.utcnow().strftime(datefmt),hostname))
        sys.exit()

    dxbi = dxbi_data.DxbiData()
    all_sites_data = dxbi.get_all_sites_data()
    auto_dx_site_assessor_table = ddb.get_ddb_table(site_assessment_table,aws_region,ddb_material_set)
    auto_dx_site_assessor_table_scan = ddb.scan_full_table(auto_dx_site_assessor_table)

    try:
        for site_assessment_record in auto_dx_site_assessor_table_scan:
            site_assessment_records.append(site_assessment_record['sim'])
    except:
        pass

    for site in all_sites_data:
        for speed in all_sites_data[site]:
            if all_sites_data[site][speed]['sim'] not in site_assessment_records:
                if all_sites_data[site][speed]['sim'] and all_sites_data[site][speed]['color'] in ['RED','YELLOW','ORANGE'] and speed != '100G':
                    command = '/apollo/env/DXDeploymentTools/bin/dx_site_assessor.py -st {} -sp {}'.format(site,speed)
                    try:
                        tts = list()
                        sim = all_sites_data[site][speed]['sim']
                        now_time = time.time()
                        start_time = datetime.datetime.utcnow().strftime(datefmt)
                        output = subprocess.run(command, shell=True, stdout=PIPE, stderr=PIPE, check=True)
                        result = output.stdout.decode()

                        for line in result.split('\n'):
                            if re.match('^\d{1,2}-\w{3}-\d{1,4}.*Ticket to Regional Border Deployment created.*',line):
                                tts.append(line.split('created: ')[1])
                            if re.match('.*To create cutsheet use.*',line):
                                cutsheet_command = line.split('To create cutsheet use ')[1] + ' -no_att'
                            if re.match('.*To create BOM use.*',line):
                                bom_command = line.split('To create BOM use ')[1] + ' -no_att'
                        if tts:
                            ticket = tts
                        else:
                            ticket = 'N/A'

                        result = re.sub('\\x1b','',result)
                        result = re.sub('\[\d{1,9}m','',result)
                        result = 'Running' + result.split('Running')[1]

                        if (cutsheet_command and bom_command):
                            cutsheet_output = subprocess.run(cutsheet_command, shell=True, stdout=PIPE, stderr=PIPE, check=True)
                            cutsheet_result = cutsheet_output.stdout.decode()
                            bom_output = subprocess.run(bom_command, shell=True, stdout=PIPE, stderr=PIPE, check=True)
                            bom_result = bom_output.stdout.decode()

                            for line in cutsheet_result.split('\n'):
                                if re.match('.*MCM.*successfully created',line):
                                    cutsheet_mcm_link = line.split()[4]
                                    cutsheet_mcm_num = cutsheet_mcm_link.split('/')[-1]
                                if re.match('.*cutsheet created.*',line):
                                    cutsheet_file = line.split()[-1]
                                    cutsheet_name = cutsheet_file.split('/')[-1]

                            for line in bom_result.split('\n'):
                                if re.match('.*MCM.*successfully created',line):
                                    bom_mcm_link = line.split()[4]
                                    bom_mcm_num = bom_mcm_link.split('/')[-1]
                                if re.match('.*BOM created.*',line):
                                    bom_file = line.split()[-1]
                                    bom_name = bom_file.split('/')[-1]

                            issue.add_attachment(sim,cutsheet_file)
                            issue.add_attachment(sim,bom_file)
                            os.remove(cutsheet_file)
                            os.remove(bom_file)
                            details = issue.get_issue_details(sim)

                            for sim_file in details.data['attachments']:
                                if cutsheet_name in sim_file['fileName']:
                                    stack = sim_file['stack']
                                    region = stack.split('-')[1]
                                    cutsheet_sim_link = 'https://maxis-file-service-' + stack + '.' + region + \
                                            '.proxy.amazon.com/issues/' + details.id + '/attachments/' + sim_file['id']
                                if bom_name in sim_file['fileName']:
                                    stack = sim_file['stack']
                                    region = stack.split('-')[1]
                                    bom_sim_link = 'https://maxis-file-service-' + stack + '.' + region + \
                                            '.proxy.amazon.com/issues/' + details.id + '/attachments/' + sim_file['id']

                            cutsheet_mcm_comment = 'Cutsheet uploaded to https://issues.amazon.com/issues/' + sim + \
                                    '\n\n' + 'To download cutsheet, use [[' + cutsheet_name + ']](' + cutsheet_sim_link + ')'
                            bom_mcm_comment = 'BOM uploaded to https://issues.amazon.com/issues/' + sim + \
                                    '\n\n' + 'To download BOM, use [[' + bom_name + ']](' + bom_sim_link + ')'

                            mcm.add_comment_to_mcm(cutsheet_mcm_num,cutsheet_mcm_comment)
                            mcm.add_comment_to_mcm(bom_mcm_num,bom_mcm_comment)


                            result = first_msg + result + '\n\nCutsheet MCM created ' + cutsheet_mcm_link + '\n\nBOM MCM created ' + bom_mcm_link

                        else:
                            result = first_msg + result + last_msg
                            cutsheet_mcm_link = 'N/A'
                            bom_mcm_link = 'N/A'

                        print(result)
                        print("{} - Updating SIM {} with site assessment results".format(datetime.datetime.utcnow().strftime(datefmt),sim))
                        issue.add_comment(sim,result)
                        finish_time = time.time()
                        end_time = datetime.datetime.utcnow().strftime(datefmt)
                        duration = finish_time - now_time
                        minutes, seconds = divmod(duration, 60)
                        run_time = str(int(minutes)) + ' minutes and ' + str(round(seconds,2)) + ' seconds'
                        site_record = {'sim':sim,'site':site,'speed':speed,'runtime':run_time,'cutsheet':cutsheet_mcm_link,'bom':bom_mcm_link,'start_time':start_time,'end_time':end_time,'host':hostname,'regional_border_tickets':ticket}
                        response = ddb.put_item_to_table(auto_dx_site_assessor_table,site_record)
                        try:
                            if response:
                                print("{} - Site assessment for SIM {} saved to DDB".format(datetime.datetime.utcnow().strftime(datefmt),sim))
                            else:
                                print("{} - Site assessment for SIM {} could not be saved to DDB".format(datetime.datetime.utcnow().strftime(datefmt),sim))
                        except:
                            print("{} - Exception: {} Site assessment for SIM {} could not be saved to DDB".format(datetime.datetime.utcnow().strftime(datefmt),sys.exc_info(),sim))

                    except:
                        print('{} - ERROR: {} Site assessment for {} at {} failed'.format(datetime.datetime.utcnow().strftime(datefmt),sys.exc_info(),site,speed))

            else:
                print("{} - Site assessment for SIM {} skipped. Record exists in DDB".format(datetime.datetime.utcnow().strftime(datefmt),all_sites_data[site][speed]['sim']))

if __name__ == '__main__':
    main()
