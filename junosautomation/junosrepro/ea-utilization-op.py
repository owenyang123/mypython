#!/usr/bin/env jpython
"""
Version:#1.3

Copyright 2018, Juniper Networks, Inc., All Rights Reserved
This script is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Avinash Reddy Singireddy, August 2016
conversion to op script - Chris Jenn, Sept 2018

ea-utilization.py - script to measure power and utilization of EA
"""
from __future__ import print_function
from __future__ import division
import sys
import getopt
import subprocess
import re


def usage():
    """ function to print usage and exit
    """
    print("To run this script you must:\n\n"
          "  1) copy script to /var/db/scripts/op/\n"
          "  2) apply the following configuration:\n"
          "     set system scripts op file ea-utilization.py "
          "arguments s description slot\n"
          "     set system scripts op file ea-utilization.py "
          "arguments c description chip\n"
          "     set system scripts language python\n"
          "  3) from cli enter:\n"
          "     op ea_utilization.py s <slot> c <chip>\n\n"
          "slot = FPC number\n"
          "chip = EA chip number")
    sys.exit(2)


def cli_command():
    """ Function to execute cli command and return output
    """
    pass


def pfe_command(slot, command):
    """ function to execute pfe command and return output
    """
    lines = []
    results = []
    line = ''
    cmd = ''

    ## pushing commands into results array
    results.append(".MPC%d()# %s"%(slot, command))

    ## execute the command"
    cmd = "cprod -A fpc%d -c \"%s\"" %(slot, command)
    lines = subprocess.check_output(cmd, shell=True)
    lines = lines.split('\n')
    for line in lines:
        line = line.replace("\x0D\x0A", "")
        line = line.replace("\t", " ")
        results.append(line)

    return results


def issue_commands(slot, chip, MPC, hmc_leakage):
    """ Issue commands function - Issues commands and capture output
    """
    test_cmd = pfe_command(slot, "show ea-asic 0")
    test_cmd = ''.join(test_cmd)
    if re.search(r'LUSS clock frequency:\s+(\d+)', test_cmd):
        # 16.1R2+ uses this format
        new_cmd_fmt = True
        cmd_output.extend(pfe_command(slot, "show ea-asic %d" %chip))
        for loop in range(0, 10):
            cmd_output.extend(pfe_command(slot, "show eachip %d disp" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d ppe rates 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show ea-asic %d cass xr rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show ea-asic %d cass idm rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show ea-asic %d cass hmc rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d filter rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d disp rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d unload rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show mqss %d drd stats" %chip))
        cmd_output.extend(pfe_command(slot, "show ea-asic %d hmcif stats" %chip))

    else:
        new_cmd_fmt = False
        cmd_output.extend(pfe_command(slot, "show eachip %d" %chip))
        for loop in range(0, 10):
            cmd_output.extend(pfe_command(slot, "show eachip %d disp" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d ppe rates 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d cass xr rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d cass idm rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d cass hmc rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d filter rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d disp rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d unload rate 1000" %chip))
        cmd_output.extend(pfe_command(slot, "show mqss %d drd stats" %chip))
        cmd_output.extend(pfe_command(slot, "show eachip %d hmcif stats" %chip))

    if MPC == "MPC7":
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-hmc-0v9" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-hmc-1v2" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-hmc-vddm-1v2" %chip))

    if MPC == "MPC8":
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc8 max20731-ea%d-hmc-0v9" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc8 max20731-ea%d-hmc-1v2" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc8 max20731-ea%d-0v906" %chip))

    if new_cmd_fmt:
        cmd_output.extend(pfe_command(slot, "show ea-asic %d xrif rate 1000" %chip))
    else:
        cmd_output.extend(pfe_command(slot, "show eachip %d xrif rate 1000" %chip))

    if MPC == "MPC7":
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-xr2-01-0v906" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-xr2-02-0v906" %chip))
        cmd_output.extend(pfe_command(slot, "diagnostic pmbus read stout-mpc7 max20731-ea%d-xr2-1v2" %chip))

    cmd_output.extend(pfe_command(slot, "show vt all"))


def get_result():
    """ Retrieve the results from issue_commands() and process them
    """
    output = []
    input_line = ""
    match = None

    input_line = cmd_output.pop(0)
    match = re.search(r'^.MPC\d+(.*)# ', input_line)
    if match is not None:
        while(1):
            try:
                input_line = cmd_output.pop(0)
            except:
                break
            match = re.search(r'^.MPC\d+(.*)# ', input_line)
            if match is not None:
                cmd_output.insert(0, input_line)
                break
            output.append(input_line)
    return output


def process_results(slot, chip, MPC, hmc_leakage):
    """ process capture results
    """
    total = 0
    active = 0
    count = 0
    context = 0
    ppe = 0
    iterations = 10
    total_idle_ = 0
    total_parcels_ = 0
    S2 = S3 = S4 = S5 = 0
    corresponding_line = ""
    index = 0
    temp_arr = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    temp = 0
    xbar_count = 0
    lt_flag = 0
    quad_count = 0
    ppe_set_count = 4
    set_count = 0
    ppe_inst_arr = []
    resource_name_arr = []
    gumem_cnt = umem_cnt = cancel_cnt = unused_cnt = pair_conflict_cnt = 0

    #To get the eachip frequency
    lines = get_result()
    for line in lines:
        match = re.search(r'LUSS clock frequency:\s+(\d+)', line)
        if match is not None:
            ea_clk_freq = int(match.group(1))

    if not ea_clk_freq:
        print("Unable to determine EA clock frequency, exiting")
        sys.exit(1)

    print("EA clock Freq: {}"
          .format(ea_clk_freq))

    total = 0
    active = 0
    for loop in range(0, 10):
        lines = get_result()
        for index in range(0, len(lines)):
            match = re.search(r'ppe_zone_enable (..):    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)', lines[index])
            if match is not None:
                # On MPC7 all the dispatch blocks are enabled for EA
                ppe_set_count = 4
                S2 = match.group(2)
                S3 = match.group(3)
                S4 = match.group(4)
                S5 = match.group(5)
                total = total + ((countbits(int(S2, 16)) + countbits(int(S3, 16)) +
                                  countbits(int(S4, 16)) + countbits(int(S5, 16))))

                corresponding_line = lines[index + 24] #change in EA

                match = re.search(r'ppe_zone_active (..):    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)', corresponding_line)
                if match is not None:
                    active = active + (countbits(int(match.group(2), 16) & int(S2, 16)) +
                                       countbits(int(match.group(3), 16) & int(S3, 16)) +
                                       countbits(int(match.group(4), 16) & int(S4, 16)) +
                                       countbits(int(match.group(5), 16) & int(S5, 16)))
            else:
                match = re.search(r'ppe_zone_enable (..):    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)', lines[index])
                if match is not None:
                    # only first two dispatch blocks are enabled for EA
                    ppe_set_count = 2
                    S2 = match.group(2)
                    S3 = match.group(3)
                    total = total + (countbits(int(S2, 16)) +
                                     countbits(int(S3, 16)))
                    corresponding_line = lines[index + 24] #change in EA
                    match = re.search(r'ppe_zone_active (..):    0x([0-9a-fA-F]+)    0x([0-9a-fA-F]+)', corresponding_line)
                    if match is not None:
                        active = active + (countbits(int(match.group(2), 16) & int(S2, 16)) +
                                           countbits(int(match.group(3), 16) & int(S3, 16)))


    if total == 0:
        print("Connection Issues")
        sys.exit()

    print("\nZone Utilization\n"
          "================\n\n"
          "  {} iterations, {} of {} opportunities, {:.2f}% utilization"
          .format(loop + 1, active, total, float(100 * active) / total))

    print("\nInstruction Utilization ({}M/s per PPE)\n"
          "=========================================="
          .format(ea_clk_freq/1000000))

    print("\n  PPE     Normal/s   % (  U /  G )   Unusable/s   % (  C / UN /  P )       Idle/s   %\n"
          "  --- ------------ --------------- ------------ -------------------- ------------ ----")

    total_inst = [0, 0, 0, 0]
    total_wait = [0, 0, 0, 0]
    total_idle = [0, 0, 0, 0]
    lines = get_result()
    ppe_count = 0
    quad_count = 0
    ppe_inst = 0
    ppe_wait = 0

    for line in lines:
        match = re.search(r'EA......PPE\s*(\d+) Perf Mon', line)
        match1 = re.search(r'EA\[%d:0]_PPE ...xss.0.'%chip, line)
        if match is not None:
            context = 1
            ppe = int(match.group(1))
            ppe_count = ppe_count + 1

        elif match1 is not None:
            context = 0

        elif context:
            if "umem_instr_count" in line:
                values = line.split()
                count = 0
                for val in values:
                    count = count + 1
                    if count == 3:
                        val = val.replace(",", "")
                        match = re.search(r'(\d+)\/sec', val)
                        if match is not None:
                            total_inst[quad_count] = total_inst[quad_count] + int(match.group(1))
                            ppe_inst = ppe_inst + int(match.group(1))
                            temp1 = int(match.group(1))
                            if "gumem_instr_count" in line:
                                gumem_cnt = temp1
                            else:
                                umem_cnt = int(match.group(1))


            elif (("cancel_instr_count" in line) or ("unused_slot_count" in line)):
                values = line.split()
                count = 0
                for val in values:
                    count = count + 1
                    if count == 3:
                        val = val.replace(",", "")
                        match = re.search(r'(\d+)\/sec', val)
                        if match is not None:
                            total_wait[quad_count] = total_wait[quad_count] + int(match.group(1))
                            ppe_wait = ppe_wait + int(match.group(1))
                            temp1 = int(match.group(1))
                            if "cancel_instr_count" in line:
                                cancel_cnt = temp1
                            else:
                                unused_cnt = int(match.group(1))

            elif "PPE Pair Conflict" in line:
                values = line.split()
                count = 0
                for val in values:
                    count = count + 1
                    if count == 5:
                        val = val.replace(",", "")
                        match = re.search(r'(\d+)\/sec', val)
                        if match is not None:
                            pair_conflict_cnt = int(match.group(1))
                ppe_idle = ea_clk_freq - (ppe_inst + ppe_wait)
                if ppe_idle < 0:
                    ppe_idle = 0
                ppe_inst_arr.append(ppe_inst)
                total_idle[quad_count] = total_idle[quad_count] + ppe_idle
                print("  {:3d} {:12d} {:3.0f}%({:4.1f}/{:4.1f}) {:12d} {:3.0f}%"
                      "({:4.1f}/{:4.1f}/{:4.1f}) {:12d} {:3.0f}%\n"
                      .format(ppe,
                              ppe_inst, ((float(ppe_inst * 100) / ea_clk_freq) + 0.5),
                              (float(umem_cnt * 100) / ea_clk_freq),
                              (float(gumem_cnt * 100) / ea_clk_freq),
                              ppe_wait, ((float(ppe_wait * 100) / ea_clk_freq) + 0.5),
                              (float(cancel_cnt * 100) / ea_clk_freq),
                              (float(unused_cnt * 100) / ea_clk_freq),
                              (float(pair_conflict_cnt * 100) / ea_clk_freq),
                              ppe_idle, ((float(ppe_idle * 100) / ea_clk_freq) + 0.5)))
                context = 1
                ppe = ppe + 1
                ppe_inst = 0
                ppe_wait = 0
                if (ppe) % 24 == 0:
                    quad_count = quad_count + 1

                ppe_count = ppe_count + 1

    print("\nLegend:\n"
          "=======\n"
          "U  Umem Instruction count\n"
          "G  GUmem Instruction count\n"
          "C  Cancelled Instruction count\n"
          "UN Unused slots count\n"
          "P  PPE pair conflicts count. "
          "This is the subset of cancel instructions count.\n\n"
          "PPE Utilization Summary\n"
          "=======================\n\n"
          "PPEs          Normal cps (%)    Unusable cps (%)           "
          "Idle cps (%)\n"
          "-----------------------------------------------------------"
          "------------")

    for i in range(0, ppe_set_count):
        print("Quad ({}) {:>15s} ({:.0f}%){:>15s} ({:.0f}%)   {:>15s} ({:.0f}%)"
              .format(i, commify(total_inst[i]),
                      (((total_inst[i] * 100) / (24 * ea_clk_freq)) + 0.5),
                      commify(total_wait[i]),
                      (((total_wait[i] * 100) / (24 * ea_clk_freq)) + 0.5),
                      commify(total_idle[i]),
                      (((total_idle[i] * 100) / (24 * ea_clk_freq)) + 0.5)))

    # XR CAE and Xbar Statistics
    print("\nXR CAE register usage:\n"
          "======================")
    lines = get_result()
    count = 0
    set_count = 0
    temp = 0
    cae_id = 0
    xr_cae_util_arr = []
    xr_xbar_src_util_arr = []
    xr_xbar_dest_util_arr = []
    lt_flag = 0
    val = -1

    for line in lines:
        match = re.search(r'EA\[%d:0].cass_xr\[(\d+)\]:'%chip, line)
        match1 = re.search(r'cae.(\d+). (hit)(.{25})(.{23})', line)
        match2 = re.search(r'cae.(\d+). (hit)(.{25})', line)
        match3 = re.search(r'cae.(\d+). (miss)(.{24})(.{23})', line)
        match4 = re.search(r'cae.(\d+). (miss)(.{24})', line)
        x_match1 = re.search(r'EA\[%d:0\].cass_xr\[(\d)\].xss\[(\d)\](.{24})(.{23})'%chip, line)
        x_match2 = re.search(r'EA\[%d:0\].cass_xr\[(\d)\].xss\[(\d)\](.{24})'%chip, line)
        x_match3 = re.search(r'EA\[%d:0\].cass_xr\[(\d)\].xds\[(\d)\](.{24})(.{23})'%chip, line)
        x_match4 = re.search(r'EA\[%d:0\].cass_xr\[(\d)\].xds\[(\d)\](.{24})'%chip, line)

        if match is not None:
            print("\nSet {}\n"
                  "~~~~~\n"
                  "\nCAE              Hit                 Miss          (%) Used\n"
                  "-----------------------------------------------------------"
                  .format(set_count))
            set_count = set_count + 1

        # Get the CAE hit statistics
        elif ((match1 is not None) or (match2 is not None)):
            if match1 is not None:
                match = match1
            elif match2 is not None:
                match = match2

            cae_id = int(match.group(1))
            if re.search(r'\s{24}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or  val == 0):
                if val == 0:
                    temp = 0
                else:
                    temp = int(match.group(1))

                if lt_flag == 1:
                    output = ("{}            < 1/sec"
                              .format(cae_id))
                    lt_flag = 0
                else:
                    output = ("{}{:>15s}/sec"
                              .format(cae_id, commify(temp)))

        # Get the CAE miss statistics
        elif ((match3 is not None) or (match4 is not None)):
            if match3 is not None:
                match = match3
            elif match4 is not None:
                match = match4

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")
                val = val.replace("<", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or  val == 0):
                if lt_flag == 1:
                    print("{}              < 1/sec{:>18d}"
                          .format(output,
                                  int((((0+temp)/ea_clk_freq) * 100) + 0.5)))
                    xr_cae_util_arr.append((0+temp))
                    lt_flag = 0
                else:
                    print("{}{:>17s}/sec{:>18d}"
                          .format(output, commify(int(match.group(1))),
                                  int((((int(match.group(1))+temp)/ea_clk_freq) * 100) + 0.5)))
                    xr_cae_util_arr.append(int(match.group(1))+ temp)

        # Get the Xbar statistics
        elif ((x_match1 is not None) or (x_match2 is not None) or \
                (x_match3 is not None) or (x_match4 is not None)):

            if x_match1 is not None:
                match = x_match1
            elif x_match2 is not None:
                match = x_match2
            elif x_match3 is not None:
                match = x_match3
            elif x_match4 is not None:
                match = x_match4

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")
                val = val.replace("<", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if val == 0:
                    temp_arr[count] = val
                else:
                    temp_arr[count] = int(match.group(1))
                count = count + 1
                if count == 4:
                    print("\nXbar           Source        (%) Used        "
                          "Destination        (%) Used\n"
                          "-----------------------------------------------"
                          "-------------------------")

                    for index in range(0, ppe_set_count):
                        if temp_arr[index] == 0:
                            output = ("{}         < 1/sec{:>15s}"
                                      .format(index,
                                              ((temp_arr[index]/ea_clk_freq)*100)))
                            xr_xbar_src_util_arr.append(temp_arr[index])
                        else:
                            output = ("{} {:>15s}/sec {:>15d}"
                                      .format(index,
                                              commify(temp_arr[index]),
                                              int(((temp_arr[index]/ea_clk_freq)*100) + 0.5)))
                            xr_xbar_src_util_arr.append(temp_arr[index])


                        if temp_arr[index + 4] == 0:
                            print("{}            < 1/sec {:>15.0f}"
                                  .format(output, (temp_arr[index+4]/ea_clk_freq)*100))
                            xr_xbar_dest_util_arr.append(temp_arr[index + 4])

                        else:
                            print("{}{:>15s}/sec {:>15d}"
                                  .format(output, commify(temp_arr[index + 4]),
                                          int(((temp_arr[index + 4]/ea_clk_freq) * 100) + 0.5)))
                            xr_xbar_dest_util_arr.append(temp_arr[index + 4])

                    count = 0

    # IDM CAE and Xbar statistic
    print("\nIDM CAE register usage:\n"
          "======================")
    lines = get_result()
    count = 0
    xbar_count = 0
    set_count = 0
    temp = 0
    cae_id = 0
    lt_flag = 0
    idm_cae_util_arr = []
    idm_xbar_src_util_arr = []
    idm_xbar_dest_util_arr = []

    for line in lines:
        # Get the CAE hit statistics
        match = re.search(r'cae.(\d+). (hit)(.{25})(.{23})', line)
        match1 = re.search(r'cae.(\d+). (hit)(.{25})', line)
        match2 = re.search(r'cae.(\d+). (miss)(.{24})(.{23})', line)
        match3 = re.search(r'cae.(\d+). (miss)(.{24})', line)
        x_match1 = re.search(r'EA\[%d:0\].cass_idm\[(\d)\].xss\[(\d)\](.{24})(.{23})'%chip, line)
        x_match2 = re.search(r'EA\[%d:0\].cass_idm\[(\d)\].xss\[(\d)\](.{24})'%chip, line)
        x_match3 = re.search(r'EA\[%d:0\].cass_idm\[(\d)\].xds\[(\d)\](.{24})(.{23})'%chip, line)
        x_match4 = re.search(r'EA\[%d:0\].cass_idm\[(\d)\].xds\[(\d)\](.{24})'%chip, line)
        if ((match is not None) or (match1 is not None)):
            if(match is None and match1 is not None):
                match = match1

            cae_id = int(match.group(1))
            if count == 0:
                print("\nSet {}\n"
                      "~~~~~\n\n"
                      "CAE              Hit                 "
                      "Miss            (%) Used\n"
                      "---------------------------------------"
                      "----------------------"
                      .format(set_count))
                set_count = set_count + 1

            if re.search(r'\s{24}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if val == 0:
                    temp = 0
                else:
                    temp = int(match.group(1))
                if lt_flag == 1:
                    output = ("{}            < 1/sec"
                              .format(cae_id))
                    lt_flag = 0
                else:
                    output = ("{}{:>15s}/sec"
                              .format(cae_id, commify(temp)))

        # Get the CAE miss statictics
        elif ((match2 is not None) or (match3 is not None)):
            if match2 is not None:
                match = match2
            elif match3 is not None:
                match = match3

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if lt_flag == 1:
                    print("{}              < 1/sec{:>20d}"
                          .format(output,
                                  int((((0 + temp) / ea_clk_freq) * 100) + 0.5)))
                    idm_cae_util_arr.append((0+temp))
                    lt_flag = 0
                else:
                    print("{}{:>17s}/sec{:>20d}"
                          .format(output,
                                  commify(int(match.group(1))),
                                  int((((int(match.group(1)) + temp) / ea_clk_freq) * 100) + 0.5)))
                    idm_cae_util_arr.append(int(match.group(1)) + temp)

            count = count + 1
            if count == 4:
                count = 0

        # Get the Xbar statistics
        elif ((x_match1 is not None) or (x_match2 is not None) or
              (x_match3 is not None) or (x_match4 is not None)):

            if x_match1 is not None:
                match = x_match1
            elif x_match2 is not None:
                match = x_match2
            elif x_match3 is not None:
                match = x_match3
            elif x_match4 is not None:
                match = x_match4

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")
                val = val.replace("<", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or  val == 0):
                if val == 0:
                    temp_arr[xbar_count] = val
                else:
                    temp_arr[xbar_count] = int(match.group(1))
                xbar_count = xbar_count + 1
                if xbar_count == 4:
                    print("\nXbar           Source        (%) Used        "
                          "Destination        (%) Used\n"
                          "-----------------------------------------------"
                          "-------------------------")

                    for index in range(0, ppe_set_count):
                        if temp_arr[index] == 0:
                            output = ("{}             < 1/sec{:>12.0f}"
                                      .format(index,
                                              ((temp_arr[index] / ea_clk_freq) * 100)))
                            idm_xbar_src_util_arr.append(temp_arr[index])
                        else:
                            output = ("{}{:>16s}/sec{:>16d}"
                                      .format(index,
                                              commify(temp_arr[index]),
                                              int(((temp_arr[index] / ea_clk_freq)*100) + 0.5)))
                            idm_xbar_src_util_arr.append(temp_arr[index])

                        if temp_arr[index + 4] == 0:
                            print("{}            < 1/sec{:>16.0f}"
                                  .format(output, (temp_arr[index + 4] / ea_clk_freq) * 100))
                            idm_xbar_dest_util_arr.append(temp_arr[index + 4])
                        else:
                            print("{}{:>15s}/sec{:16d}"
                                  .format(output, commify(temp_arr[index + 4]),
                                          int(((temp_arr[index + 4] / ea_clk_freq) * 100) + 0.5)))
                            idm_xbar_dest_util_arr.append(temp_arr[index + 4])

                    xbar_count = 0

    # HMC CAE and Xbar statitics
    print("\nHMC CAE register usage:\n"
          "=======================")
    set_count = 0
    lines = get_result()
    set_count = 0
    count = 0
    lt_flag = 0
    hmc_cae_util_arr = []
    hmc_xbar_src_util_arr = []
    hmc_xbar_dest_util_arr = []
    for line in lines:
        match = re.search(r'EA\[%d:0].cass_hmc\[(\d+)\]:'%chip, line)
        match1 = re.search(r'cae.(\d+). (hit)(.{25})(.{23})', line)
        match2 = re.search(r'cae.(\d+). (hit)(.{25})', line)
        match3 = re.search(r'cae.(\d+). (miss)(.{24})(.{23})', line)
        match4 = re.search(r'cae.(\d+). (miss)(.{24})', line)
        x_match1 = re.search(r'EA\[%d:0\].cass_hmc\[(\d)\].xss\[(\d)\](.{24})(.{23})'%chip, line)
        x_match2 = re.search(r'EA\[%d:0\].cass_hmc\[(\d)\].xss\[(\d)\](.{24})'%chip, line)
        x_match3 = re.search(r'EA\[%d:0\].cass_hmc\[(\d)\].xds\[(\d)\](.{24})(.{23})'%chip, line)
        x_match4 = re.search(r'EA\[%d:0\].cass_hmc\[(\d)\].xds\[(\d)\](.{24})'%chip, line)

        if match is not None:
            print("\nSet {}\n"
                  "~~~~~\n\n"
                  "CAE              Hit                 "
                  "Miss          (%) Used\n"
                  "---------------------------------------"
                  "--------------------"
                  .format(set_count))
            set_count = set_count + 1

        # Get the CAE hit statistics
        elif ((match1 is not None) or (match2 is not None)):
            if match1 is not None:
                match = match1
            elif match2 is not None:
                match = match2

            cae_id = int(match.group(1))
            if re.search(r'\s{24}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if val == 0:
                    temp = 0
                else:
                    temp = int(match.group(1))

                if lt_flag == 1:
                    output = ("{}            < 1/sec"
                              .format(cae_id))
                    lt_flag = 0
                else:
                    output = ("{}{:>15s}/sec"
                              .format(cae_id, commify(temp)))

        # Get the CAE miss statistics
        elif ((match3 is not None) or (match4 is not None)):
            if match3 is not None:
                match = match3
            elif match4 is not None:
                match = match4

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
                lt_flag = 1
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if lt_flag == 1:
                    print("{}            < 1/sec{:>15d}"
                          .format(output,
                                  int((((0 + temp) / ea_clk_freq) * 100) + 0.5)))
                    hmc_cae_util_arr.append((0 + temp))
                    lt_flag = 0
                else:
                    print("{}{:>17s}/sec{:>18d}"
                          .format(output,
                                  commify(int(match.group(1))),
                                  int((((int(match.group(1)) + temp) / ea_clk_freq) * 100) + 0.5)))
                    hmc_cae_util_arr.append(int(match.group(1)) + temp)

        # Get the Xbar statistics
        elif ((x_match1 is not None) or (x_match2 is not None) or
              (x_match3 is not None) or (x_match4 is not None)):
            if x_match1 is not None:
                match = x_match1
            elif x_match2 is not None:
                match = x_match2
            elif x_match3 is not None:
                match = x_match3
            elif x_match4 is not None:
                match = x_match4

            if re.search(r'\s{23}0', match.group(3)):
                val = 0
            elif re.search(r'< 1\/sec', match.group(4)):
                val = 0
            else:
                val = match.group(4)
                val = val.replace(",", "")
                val = val.replace(" ", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if val == 0:
                    temp_arr[count] = val
                else:
                    temp_arr[count] = int(match.group(1))
                count = count + 1
                if count == 4:
                    print("\nXbar           Source        (%) Used        "
                          "Destination        (%) Used\n"
                          "-----------------------------------------------"
                          "-------------------------")

                    for index in range(0, ppe_set_count):
                        if temp_arr[index] == 0:
                            output = ("{}             < 1/sec{:>16.0f}"
                                      .format(index,
                                              ((temp_arr[index]/ea_clk_freq)*100)))
                            hmc_xbar_src_util_arr.append(temp_arr[index])
                        else:
                            output = ("{}{:>16s}/sec{:>16.0f}"
                                      .format(index,
                                              commify(temp_arr[index]),
                                              int(((temp_arr[index] / ea_clk_freq) * 100) + 0.5)))
                            hmc_xbar_src_util_arr.append(temp_arr[index])

                        if temp_arr[index + 4] == 0:
                            print("{}            < 1/sec{:>16.0f}"
                                  .format(output, (temp_arr[index + 4] / ea_clk_freq) * 100))
                            hmc_xbar_dest_util_arr.append(temp_arr[index + 4])
                        else:
                            print("{}{:>15s}/sec{:>16.0f}"
                                  .format(output, commify(temp_arr[index + 4]),
                                          int(((temp_arr[index+4]/ea_clk_freq) * 100) + 0.5)))
                            hmc_xbar_dest_util_arr.append(temp_arr[index + 4])

                    count = 0

    # FLT Rates
    flt_xbar_src_util_arr = [0, 0, 0, 0, 0, 0, 0, 0]
    flt_xbar_dst_util_arr = [0, 0, 0, 0, 0, 0, 0, 0]
    print("\nFilter Block (FLT) Usage\n"
          "========================")
    lines = get_result()
    flt_xtxns = 0
    beta0_lkup_cnt = 0
    beta1_lkup_cnt = 0
    alpha_lkup_cnt = 0
    cv_lkup_cnt = 0

    for line in lines:

        line = line.replace(",", "")
        line = line.replace("< 1", "0")

        # Get the FLT Xtxns stats
        match = re.search(r'\s+xif_xtxn\s+(\d+)', line)
        if match is not None:
            flt_xtxns = 0
        match = re.search(r'\s+xif_xtxn\s+(\d+)\s+(\d+)\/sec', line)
        if match is not None:
            flt_xtxns = int(match.group(2))

        # Get the Alpha Lookup stats
        match = re.search(r'pf0_1_alpha\[1\]\.bft_lkp\s+(\d+)', line)
        if match is not None:
            alpha_lkup_cnt = 0

        match = re.search(r'pf0_1_alpha\[1\]\.bft_lkp\s+(\d+)\s+(\d+)\/sec', line)
        if match is not None:
            alpha_lkup_cnt = int(match.group(2))

        # Get the Beta0 Lookup stats
        match = re.search(r'pf2_3_beta\[0\]\.lkp\s+(\d+)', line)
        if match is not None:
            beta0_lkup_cnt = 0

        match = re.search(r'pf2_3_beta\[0\]\.lkp\s+(\d+)\s+(\d+)\/sec', line)
        if match is not None:
            beta0_lkup_cnt = int(match.group(2))

        # Get the Beta1 Lookup stats
        match = re.search(r'pf2_3_beta\[1\]\.lkp\s+(\d+)', line)
        if match is not None:
            beta1_lkup_cnt = 0

        match = re.search(r'pf2_3_beta\[1\]\.lkp\s+(\d+)\s+(\d+)\/sec', line)
        if match is not None:
            beta1_lkup_cnt = int(match.group(2))

       # Get CV Lookup stats
        match = re.search(r'cv_lkp\s+(\d+)', line)
        if match is not None:
            cv_lkup_cnt = 0

        match = re.search(r'cv_lkp\s+(\d+)\s+(\d+)\/sec', line)
        if match is not None:
            cv_lkup_cnt = int(match.group(2))

        match = re.search(r'EA\[%d:0\].filter.xss\[(\d+)\]\s+(\d+)'%chip, line)
        if match is not None:
            flt_xbar_src_util_arr[int(match.group(1))] = 0

        match = re.search(r'EA\[%d:0\].filter.xss\[(\d+)\]\s+(\d+)\s+(\d+)\/sec'%chip, line)
        if match is not None:
            flt_xbar_src_util_arr[int(match.group(1))] = int(match.group(2))

        match = re.search(r'EA\[%d:0\].filter.xds\[(\d+)\]\s+(\d+)'%chip, line)
        if match is not None:
            flt_xbar_dst_util_arr[int(match.group(1))] = 0

        match = re.search(r'EA\[%d:0\].filter.xds\[(\d+)\]\s+(\d+)\s+(\d+)\/sec'%chip, line)
        if match is not None:
            flt_xbar_dst_util_arr[int(match.group(1))] = int(match.group(2))


    print("\nFilter-Block       Counts/sec   (%)Used\n"
          "---------------------------------------\n"
          "XTXN             {:>12s}   {:>7d}\n"
          "CV Lkup          {:>12s}   {:>7d}\n"
          "ALPHA Lkup       {:>12s}   {:>7d}\n"
          "BETA0 Lkup       {:>12s}   {:>7d}\n"
          "BETA1 Lkup       {:>12s}   {:>7d}\n"
          "\nXbar           Source        (%) Used        "
          "Destination        (%) Used\n"
          "-----------------------------------------------"
          "-------------------------"
          .format(commify(flt_xtxns), int((flt_xtxns/ea_clk_freq)*100),
                  commify(cv_lkup_cnt), int((cv_lkup_cnt/ea_clk_freq)*100),
                  commify(alpha_lkup_cnt), int((alpha_lkup_cnt/ea_clk_freq)*100),
                  commify(beta0_lkup_cnt), int((beta0_lkup_cnt/ea_clk_freq)*100),
                  commify(beta0_lkup_cnt), int((beta1_lkup_cnt/ea_clk_freq)*100)))

    for index in range(0, ppe_set_count):
        if flt_xbar_src_util_arr[index] == 0:
            output = ("{}             < 1/sec{:>16.0f}"
                      .format(index,
                              ((flt_xbar_src_util_arr[index] / ea_clk_freq) * 100)))
        else:
            output = ("{} {:>15s}/sec {:>15.0f}"
                      .format(index,
                              commify(flt_xbar_src_util_arr[index]),
                              int(((flt_xbar_src_util_arr[index] / ea_clk_freq) * 100) + 0.5)))

        if flt_xbar_dst_util_arr[index] == 0:
            print("{}            < 1/sec {:>15.0f}"
                  .format(output, (flt_xbar_dst_util_arr[index + 4] / ea_clk_freq) * 100))
        else:
            print("{}{:>15s}/sec {:>15.0f}"
                  .format(output, commify(flt_xbar_dst_util_arr[index]),
                          int(((flt_xbar_dst_util_arr[index] / ea_clk_freq) * 100) + 0.5)))

    # Parcel Count Statistics
    print("\nParcel rates (parcels/sec)\n"
          "==========================")
    count = 0
    sum_ = 0
    lines = get_result()
    set_count = 0
    for line in lines:

        # Get the parcel count statistics for type 0, 1 & 2 parcels
        match = re.search(r'parcel_count\[\d\](.{24})(.{23})', line)
        match1 = re.search(r'parcel_count\[\d\](.{24})', line)
        match2 = re.search(r'parcel_count\[3\](.{24})(.{23})', line)


        if (((match is not None) or (match1 is not None)) and (match2 is None)):

            if((match is None) and (match1 is not None)):
                match = match1

            if re.search(r'\s{23}0', match.group(1)):
                val = 0
            else:
                val = match.group(2)
                val = val.replace(",", "")
                val = val.replace(" ", "")
                val = val.replace("<", "")

            match = re.search(r'(\d+)\/sec', str(val))
            if (match is not None or val == 0):
                if val == 0:
                    temp_arr[count] = 0
                else:
                    temp_arr[count] = float(match.group(1))
                if count == 2:
                    sum_ = temp_arr[count] + temp_arr[(count-1)] + temp_arr[(count-2)]
                    print("Parcel Rate                     : {}/sec"
                          .format(commify(sum_)))
                    print("Average Instructions per parcel : {:<.2f}"
                          .format(total_inst[set_count]/sum_))
                    print("Average wait cycles per parcel  : {:<.2f}"
                          .format(total_idle[set_count]/sum_))
                    print("Average cycles per parcel       : {:<.2f}"
                          .format((total_inst[set_count]+total_idle[set_count])/sum_))
                    count = 0
                    set_count = set_count + 1
                else:
                    if count == 0:
                        print("\nSet {}\n"
                              .format(set_count))
                    count = count + 1

    # Unload Rate
    print("\nUnload rates (parcels/sec)\n"
          "==========================")
    lines = get_result()
    set_count = 0
    for line in lines:

        # Get the parcel unload statistics
        if re.search(r'chan\[0\].total_pkt', line):
            values = line.split()
            for val in values:
                match = re.search(r'(\d+)\/sec', val)
                if match is not None:
                    print("Quad {} : {:>17}"
                          .format(set_count, val))
                    set_count = set_count + 1

    total_ppe_inst = 0
    for i in range(0, ppe_set_count):
        total_ppe_inst = total_ppe_inst + total_inst[i]

    # DRD stats
    print("\nDRD stats (pps)\n"
          "===============")
    lines = get_result()
    for  line in lines:

        # Get the packet rate
        if "Packets" in line:
            values = line.split()
            print("\nDRD[{}] packet rate  : {} pps"
                  .format(values[0], commify(float(values[3]))))
            if int(values[3]) != 0:
                print("PPE packet Trace[{}] : {}"
                      .format(values[0], commify(total_ppe_inst / float(values[3]))))

    hmc_wr_req_rate = [0, 0, 0, 0, 0, 0]
    hmc_rd_req_rate = [0, 0, 0, 0, 0, 0]

    #HMC usage extraction
    print("\nHMC usage for {} (max rate per links {} MF/s)\n"
          "===================================================="
          .format(MPC, "1,875" if(MPC == "MPC8") else "1,562.5"))
    lines = get_result()
    for line in lines:
        if "req_cnt" in line:
            values = line.split()
            if values[1] == "wr_req_cnt":
                hmc_wr_req_rate[int(values[0])] = int(values[3])
            if values[1] == "rd_req_cnt":
                hmc_rd_req_rate[int(values[0])] = int(values[3])

    #HMC per link usage
    if MPC == "MPC8":
        for i in range(0, 6):
            # 15Gb X 16 lanes / 8(bytes) X 16B(Flits) = 15G/8 fits per second = 1875 M flits/second
            print("HMC link {} utilization: {:.2f}%, {:>14s} Total F/s, {:>14s} WR F/s, {:>14s} RD F/s"
                  .format(i, (float(hmc_wr_req_rate[i] + hmc_rd_req_rate[i]) / 18750000),
                          commify(hmc_wr_req_rate[i] + hmc_rd_req_rate[i]),
                          commify(hmc_wr_req_rate[i]), commify(hmc_rd_req_rate[i])))

    if MPC == "MPC7":
        for i in range(0, 4):
            # 12.5Gb X 16 lanes / 8(bytes) X 16B(Flits) = 12.5G/8 fits per second = 1562.5 M flits/second
            print("HMC link {} utilization: {:.2f}%, {:>14s} Total F/s, {:>14s} WR F/s, {:>14s} RD F/s"
                  .format(i, (float(hmc_wr_req_rate[i] + hmc_rd_req_rate[i]) / 15625000),
                          commify(hmc_wr_req_rate[i] + hmc_rd_req_rate[i]),
                          commify(hmc_wr_req_rate[i]), commify(hmc_rd_req_rate[i])))

    iout = 0
    vout = 0

    # HMC power usage
    print("\nHMC power\n"
          "=========")
    lines = get_result()
    for line in lines:
        if "VT" in line:
            values = line.split()
            print(values[3])

        if "VOUT" in line:
            values = line.split()
            vout = float(values[3])

        if "IOUT" in line:
            values = line.split()
            iout = float(values[5])

    hmc_0v9 = vout * iout
    print(hmc_0v9)
    lines = get_result()
    for line in lines:
        if "VT" in line:
            values = line.split()
            print(values[3])

        if "VOUT" in line:
            values = line.split()
            vout = float(values[3])

        if "IOUT" in line:
            values = line.split()
            iout = float(values[5])

    hmc_1v2 = vout * iout
    print(hmc_1v2)
    lines = get_result()
    for line in lines:
        if "VT" in line:
            values = line.split()
            print(values[3])

        if "VOUT" in line:
            values = line.split()
            vout = float(values[3])

        if "IOUT" in line:
            values = line.split()
            iout = float(values[5])

    hmc_vdd = vout * (iout + hmc_leakage)
    print("{}\nhmc_leakge provided : {}"
          .format(hmc_vdd, hmc_leakage))
    if MPC == "MPC7":
        print("per HMC power(MPC7 only): {} W"
              .format((float(hmc_vdd + hmc_0v9 + hmc_1v2))/2))

    #XR usage
    nop_read = []
    nop_write = []
    read = []
    write = []
    cycle = []
    print("\nXR2 bandwidth usage\n"
          "===================")
    lines = get_result()
    count = 0
    for line in lines:
        if re.search(r'^ *cycle', line):
            values = line.split()
            cycle.append(values[2])

        if "NOP Read" in line:
            values = line.split()
            nop_read.append(values[3])

        if "NOP Write" in line:
            values = line.split()
            nop_write.append(values[3])

        if re.search(r'^ *Read', line):
            values = line.split()
            read.append(values[2])

        if "Write Int" in line:
            values = line.split()
            write.append(values[3])

    for i in range(0, 4):
        print("XRIF[{}]:"
              .format(i))
        nop_read[i] = str(nop_read[i]).replace(",", "")
        nop_write[i] = str(nop_write[i]).replace(",", "")
        read[i] = str(read[i]).replace(",", "")
        write[i] = str(write[i]).replace(",", "")
        cycle[i] = str(cycle[i]).replace(",", "")
        nop_read[i] = float(nop_read[i])
        nop_write[i] = float(nop_write[i])
        read[i] = float(read[i])
        write[i] = float(write[i])
        cycle[i] = float(cycle[i])
        print("  READ : Active : {:2.2f}%, NOP: {:2.2f}\n"
              "  WRITE: Active : {:2.2f}%, NOP: {:2.2f}"
              .format(((read[i] * 100) / 2) / cycle[i], (((nop_read[i] / 2) / cycle[i]) * 100),
                      (write[i] * 100) / cycle[i], (nop_write[i] * 100) / cycle[i]))

    if MPC == "MPC7":
        # XR2 power usage
        print("\nXR2 power\n"
              "=========")
        lines = get_result()
        for line in lines:
            if "VT" in line:
                values = line.split()
                print(values[3])

            if "VOUT" in line:
                values = line.split()
                vout = float(values[3])

            if "IOUT" in line:
                values = line.split()
                iout = float(values[5])

        xr2_0v9_0 = vout * iout
        print(xr2_0v9_0)

        lines = get_result()
        for line in lines:
            if "VT" in line:
                values = line.split()
                print(values[3])

            if "VOUT" in line:
                values = line.split()
                vout = float(values[3])

            if "IOUT" in line:
                values = line.split()
                iout = float(values[5])

        xr2_0v9_1 = vout * iout
        print(xr2_0v9_1)

        lines = get_result()
        for line in lines:
            if "VT" in line:
                values = line.split()
                print(values[3])

            if "VOUT" in line:
                values = line.split()
                vout = float(values[3])

            if "IOUT" in line:
                values = line.split()
                iout = float(values[5])

        xr2_1v2 = vout * iout
        print(xr2_1v2)
        print("\nXR2_0 power(MPC7 only): {} W\n"
              "XR2_1 power(MPC7 only): {} W"
              .format((xr2_0v9_0 + (xr2_1v2/2)),
                      (xr2_0v9_1 + (xr2_1v2/2))))

    # vt data
    print("\n\nCore power\n"
          "==========")
    lines = get_result()
    for line in lines:
        # Get the packet rate
        if "EA" in line:
            values = line.split()
            print("{} Core power   : {} W"
                  .format(values[2], values[7]))

    #List of resources
    #As new resources are monitored their names may have to be added here
    resource_name_arr = ["PPE",
                         "XR CAE",
                         "XR Xbar Src",
                         "XR Xbar Dest",
                         "IDM CAE",
                         "IDM Xbar Src",
                         "IDM Xbar Dest",
                         "HMC CAE",
                         "HMC Xbar Src",
                         "HMC Xbar Dest"]

    print("\nResource Summary\n"
          "================\n\n"
          "Resource        Max Instance Utilization    Average Utilization    "
          "Min Instance Utilization\n"
          "------------------------------------------------------------------"
          "-------------------------")

    ppe_avg_util = ((sum(ppe_inst_arr) * 100) / ((ppe_set_count * 24) * ea_clk_freq))
    print_resource_util_summary(ea_clk_freq, resource_name_arr[0],
                                ppe_set_count * 24, ppe_inst_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[1], 16,
                                xr_cae_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[2], 16,
                                xr_xbar_src_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[3], 16,
                                xr_xbar_dest_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[4], 8,
                                idm_cae_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[5], 8,
                                idm_xbar_src_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[6], 8,
                                idm_xbar_dest_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[7], 6,
                                hmc_cae_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[8], 8,
                                hmc_xbar_src_util_arr)
    print_resource_util_summary(ea_clk_freq, resource_name_arr[9], 8,
                                hmc_xbar_dest_util_arr)

def print_resource_util_summary(ea_clk_freq, resource_name, div_factor, arr):
    """ print a summary of resource utilization
    """
    if arr:
        max_ = max(arr)
        sum_ = sum(arr)
        min_ = min(arr)
    else:
        max_ = 0
        sum_ = 0
        min_ = 0

    maxm = ((max_ * 100) / ea_clk_freq)
    if ((resource_name != "PPE") and (maxm > 94) and (ppe_avg_util < 90)):
        output = ("{:13s}         (HOT BANKING)"
                  .format(resource_name))
    else:
        output = ("{:13s}                      "
                  .format(resource_name))

    print("{}{:4.1f}%                  {:4.1f}%                       {:4.1f}%"
          .format(output, (float(max_ * 100) / ea_clk_freq),
                  (float(sum_ * 100) / (div_factor * ea_clk_freq)),
                  (float(min_ * 100) / ea_clk_freq)))


def commify(n):
    """ commify a given number
        >>> commify(1)
        '1'
        >>> commify(123)
        '123'
        >>> commify(1234)
        '1,234'
        >>> commify(1234567890)
        '1,234,567,890'
        >>> commify(123.0)
        '123.0'
        >>> commify(1234.5)
        '1,234.5'
        >>> commify(1234.56789)
        '1,234.56789'
        >>> commify('%.2f' % 1234.5)
        '1,234.50'
        >>> commify(None)
        >>>
    """
    if n is None:
        return None
    n = str(n)
    if '.' in n:
        dollars, cents = n.split('.')
    else:
        dollars, cents = n, None

    r = []
    for i, c in enumerate(str(dollars)[::-1]):
        if i and (not i % 3):
            r.insert(0, ',')
        r.insert(0, c)
    out = ''.join(r)
    if cents:
        out += '.' + cents
    return out


def countbits(number):
    """ countbits -count number of ones
    """
    count = 0

    for bit in range(0, 32):
        if number & (1 << bit):
            count = count + 1

    return count


def main(slot, chip, MPC, hmc_leakage):
    """ main event
    """
    issue_commands(slot, chip, MPC, hmc_leakage)
    process_results(slot, chip, MPC, hmc_leakage)


if __name__ == "__main__":

    hmc_leakage = 0
    chip = None
    slot = None
    MPC = None
    version_data = subprocess.Popen('head -3 %s | tail -1' % (sys.argv[0]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = version_data.stdout.readlines()[0].rstrip()
    print("Version # {}"
          .format(ret.split('#')[1]))

    # Parse the arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:c:l:h", [])
    except getopt.GetoptError:
        print("ERROR :: Seems to be an error with input arguments. Please check usage below")
        usage()
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in "-s":
            slot = int(arg)
        elif opt in "-c":
            chip = int(arg)
        elif opt in "-l":
            hmc_leakage = float(arg)

    if slot < 0 or slot > 19:
        print("ERROR :: slot number missing or invalid")
        usage()

    cmd = ('cli -c \'show chassis hardware\' | grep "FPC {} "'
           .format(slot))
    try:
        line = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        print("ERROR :: fpc slot is likely empty")
        usage()

    if re.search(r'MPC7', line):
        MPC = "MPC7"
    elif re.search(r'MPC8', line):
        MPC = "MPC8"
    elif re.search(r'MPC9', line):
        MPC = "MPC8"

    if not MPC:
        print("ERROR :: fpc in slot {} is not an MPC7, 8 or 9")
        usage()

    if MPC == "MPC7":
        if chip < 0 or chip > 1:
            print("ERROR :: chip number missing or invalid")
            usage()
    elif MPC == "MPC8":
        if chip < 0 or chip > 3:
            print("ERROR :: chip number missing or invalid")
            usage()

    cmd_output = []
    ea_clk_freq = None
    ppe_avg_util = 0

    # Start executing
    main(slot, chip, MPC, hmc_leakage)
