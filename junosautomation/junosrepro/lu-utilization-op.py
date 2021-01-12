#!/usr/bin/env jpython
"""
Copyright 2019, Juniper Networks, Inc., All Rights Reserved
This script is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

lu-utilization-op.py - op script to measure utilization of lu
"""
from __future__ import print_function
from __future__ import division
import sys
import getopt
import subprocess
import re

version = 1.0


def usage():
    """ function to print usage and exit
    """
    print(
        "To run this script you must:\n\n"
        "  1) copy script to /var/db/scripts/op/\n"
        "  2) apply the following configuration:\n"
        "     set system scripts op file lu-utilization-op.py "
        "arguments s description slot\n"
        "     set system scripts op file lu-utilization-op.py "
        "arguments p description pfe\n"
        "     set system scripts language python\n"
        "  3) from cli enter:\n"
        "     op lu_utilization-op.py s <slot> p <pfe>\n\n"
        "slot = FPC number\n"
        "pfe = PFE number\n"
    )
    sys.exit(2)


def shell_command(cmd):
    """ Function to execute cli command and return output
    """
    lines = ""
    exit_code = True
    try:
        lines = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        exit_code = False
    result = lines.split("\n")
    if debug:
        print("cmd = {}".format(cmd))
        print("output = \n{}".format(lines))
    return exit_code, result


def pfe_command(slot, slot_str, command):
    """ function to execute pfe command and return output
    """
    result = []
    lines = ""
    exit_code = True

    ## pushing commands into results array
    result.append("NPC{}()# {}".format(slot, command))

    ## execute the command
    cmd = 'cprod -A {} -c "{}"'.format(slot_str, command)
    try:
        lines = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        exit_code = False
    split_lines = lines.split("\n")

    for line in split_lines:
        line = line.replace("\x0D\x0A", "")
        line = line.replace("\t", " ")
        result.append(line)
    if debug:
        print("cmd = {}".format(cmd))
        print("output = \n{}".format(lines))
    return exit_code, result


def issue_commands(slot, slot_str, lu):
    """ Issue commands function - Issues commands and capture output
    """
    for loop in range(0, 10):
        exit_code, result = pfe_command(
            slot, slot_str, "show luchip {} disp".format(lu)
        )
        if exit_code:
            cmd_output.extend(result)
        else:
            print("ERROR :: unable to retrieve 'show luchip {} disp' output".format(lu))
            sys.exit(1)
    exit_code, result = pfe_command(
        slot, slot_str, "show luchip {} rate 100".format(lu)
    )
    if exit_code:
        cmd_output.extend(result)
    else:
        print("ERROR :: unable to retrieve 'show luchip {} rate 100' output".format(lu))
        sys.exit(1)


def get_result():
    """ Retrieve the results from issue_commands() and process them
    """
    output = []
    input_line = ""
    match = None

    input_line = cmd_output.pop(0)
    match = re.search(r"^NPC\d+(.*)# ", input_line)
    if match is not None:
        while 1:
            try:
                input_line = cmd_output.pop(0)
            except:
                break
            match = re.search(r"^NPC\d+(.*)# ", input_line)
            if match is not None:
                cmd_output.insert(0, input_line)
                break
            output.append(input_line)
    return output


def process_results(slot, slot_str, lu):
    """ process capture results
    """
    print("LU clock Freq: {}".format(lu_clk_freq))

    total = 0
    active = 0
    for loop in range(0, 10):
        lines = get_result()
        for index in range(0, len(lines)):
            match = re.search(
                r"Zone Enable Mask 0x([0-9a-fA-F]+)  \(0x([0-9a-fA-F]+)\)", lines[index]
            )
            if match is not None:
                S1 = match.group(1)
                S2 = match.group(2)
                total = total + (countbits(int(S1, 16)))
                active = active + (countbits(int(S2, 16) & int(S1, 16)))

    if total == 0:
        print("Unable to obtain the Zone Enable Mask details")
        sys.exit()

    print(
        "\nZone Utilization\n"
        "================\n"
        "  10 iterations, {} of {} opportunities, {:4.2f}% utilization\n".format(
            active, total, float(100 * active) / total
        )
    )

    print(
        "\nInstruction Utilization ({}M/s per PPE)\n"
        "==========================================\n".format(lu_clk_freq / 1000000)
    )

    print(
        "\n    PPE     Instruction %Max        Unusable %Max            Idle %Max\n"
        "  ----- --------------- ---- --------------- ---- --------------- ----\n"
    )

    total_umem = 0
    total_gumem = 0
    total_cancel = 0
    total_unused = 0
    total_parcels = 0
    ppe = 0
    umem = 0
    gumem = 0
    cancel = 0
    unused = 0

    lines = get_result()
    for line in lines:
        # Although we asked for a sample window of a certain size,
        # the command will tell us the actual window size.  We should
        # adjust the values read to the actual window size because
        # the maximums are relative the precise period.
        match = re.search(r"Aggregate Counts\s+Rates\s+([0-9.?]+)\s+(\w+)", line)
        if match is not None:
            period = match.group(1)
            if match.group(2) == "sec":
                period = period * 1000
            period = int(period)

        match = re.search(r"parcel_count\[\d+\]\s+\d+\s+(\d+)\/sec", line)
        if match is not None:
            parcel_count = int(match.group(1))
            total_parcels += int(parcel_count * (sample / period))

        match = re.search(r"umem_instr_count\s+\d+\s+(\d+)\/sec", line)
        if match is not None:
            umem_instr_count = int(match.group(1))
            umem = int(umem_instr_count * (sample / period))

        match = re.search(r"gumem_instr_count\s+\d+\s+(\d+)\/sec", line)
        if match is not None:
            gumem_instr_count = int(match.group(1))
            gumem = int(gumem_instr_count * (sample / period))

        match = re.search(r"cancel_instr_count\s+\d+\s+(\d+)\/sec", line)
        if match is not None:
            cancel_instr_count = int(match.group(1))
            cancel = int(cancel_instr_count * (sample / period))

        match = re.search(r"unused_slot_count\s+\d+\s+(\d+)\/sec", line)
        if match is not None:
            unused_slot_count = int(match.group(1))
            unused = int(unused_slot_count * (sample / period))
            inst = umem + gumem
            wait = cancel + unused
            idle = lu_clk_freq - (inst + wait)
            total_umem += umem
            total_gumem += gumem
            total_cancel += cancel
            total_unused += unused

            print(
                "{:>7} {:>15s} {:>3.0f}% {:>15s} {:>3.0f}% {:>15s} {:>3.0f}%".format(
                    ppe,
                    commify(inst),
                    ((inst * 100) / lu_clk_freq),
                    commify(wait),
                    ((wait * 100) / lu_clk_freq),
                    commify(idle),
                    ((idle * 100) / lu_clk_freq),
                )
            )

            # Prepare for next PPE
            ppe += 1
            umem = 0
            gumem = 0
            cancel = 0
            unused = 0

    total_inst = total_umem + total_gumem
    total_wait = total_cancel + total_unused
    total_idle = (lu_clk_freq * ppe) - (total_inst + total_wait)
    print("  ----- --------------- ---- --------------- ---- --------------- ----")
    print(
        "  Total {:>15s} {:>3.0f}% {:>15s} {:>3.0f}% {:>15s} {:>3.0f}%".format(
            commify(total_inst),
            total_inst * 100 / (lu_clk_freq * ppe),
            commify(total_wait),
            total_wait * 100 / (lu_clk_freq * ppe),
            commify(total_idle),
            total_idle * 100 / (lu_clk_freq * ppe),
        )
    )

    print(
        "\n  Summary                  Slots/s    %\n"
        "  ---------------- --------------- ----\n"
        "  Instructions     {:>15s} {:>3.0f}%\n"
        "    umem           {:>15s} {:>3.0f}%\n"
        "    gumem          {:>15s} {:>3.0f}%\n"
        "  Unusable         {:>15s} {:>3.0f}%\n"
        "    cancels        {:>15s} {:>3.0f}%\n"
        "    unused         {:>15s} {:>3.0f}%\n"
        "  Idle             {:>15s} {:>3.0f}%\n".format(
            commify(total_inst),
            total_inst * 100 / (lu_clk_freq * ppe),
            commify(total_umem),
            total_umem * 100 / (lu_clk_freq * ppe),
            commify(total_gumem),
            total_gumem * 100 / (lu_clk_freq * ppe),
            commify(total_wait),
            total_wait * 100 / (lu_clk_freq * ppe),
            commify(total_cancel),
            total_cancel * 100 / (lu_clk_freq * ppe),
            commify(total_unused),
            total_unused * 100 / (lu_clk_freq * ppe),
            commify(total_idle),
            total_idle * 100 / (lu_clk_freq * ppe),
        )
    )

    policers = 0
    counters = 0
    controller = 0
    context = None
    rate = 0
    peak = 0
    reset_controller = True
    rldram_reads = dict()
    rldram_writes = dict()
    rldram_total = dict()
    ddr_reads = dict()
    ddr_writes = dict()
    ddr_total = dict()
    emc_reads = dict()
    emc_writes = dict()
    emc_total = dict()
    imc_reads = dict()
    imc_writes = dict()
    imc_total = dict()
    rldram_ddr_sections = (
        rldram_reads,
        rldram_writes,
        rldram_total,
        ddr_reads,
        ddr_writes,
        ddr_total,
    )

    for section in rldram_ddr_sections:
        section[controller] = dict()
        section[controller][8] = int()

    for line in lines:
        if re.search(r"emc_(\d)_reads\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"emc_(\d)_reads\s+\d+\s+([<])*\s(\d+)\/sec", line)
            controller = int(match.group(1))
            less_than = match.group(2)
            rate = int(match.group(3))
            if less_than:
                rate = 0
            emc_reads[controller] = rate
            emc_total[controller] = rate
        elif re.search(r"emc_(\d)_writes\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"emc_(\d)_writes\s+\d+\s+([<])*\s(\d+)\/sec", line)
            controller = int(match.group(1))
            less_than = match.group(2)
            rate = int(match.group(3))
            if less_than:
                rate = 0
            emc_writes[controller] = rate
            emc_total[controller] += rate
        elif re.search(r"imc_(\d)_reads\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"imc_(\d)_reads\s+\d+\s+([<])*\s(\d+)\/sec", line)
            controller = int(match.group(1))
            less_than = match.group(2)
            rate = int(match.group(3))
            if less_than:
                rate = 0
            imc_reads[controller] = rate
            imc_total[controller] = rate
        elif re.search(r"imc_(\d)_writes\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"imc_(\d)_writes\s+\d+\s+([<])*\s(\d+)\/sec", line)
            controller = int(match.group(1))
            less_than = match.group(2)
            rate = int(match.group(3))
            if less_than:
                rate = 0
            imc_writes[controller] = rate
            imc_total[controller] += rate
        elif re.search(r"plct_p0_xtxn\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"plct_p0_xtxn\s+\d+\s+([<])*\s(\d+)\/sec", line)
            less_than = match.group(1)
            policers = int(match.group(2))
            if less_than:
                policers = 0
        elif re.search(r"plct_p1_xtxn\s+\d+\s+[<]*\s(\d+)\/sec", line):
            match = re.search(r"plct_p1_xtxn\s+\d+\s+([<])*\s(\d+)\/sec", line)
            less_than = match.group(1)
            counters = int(match.group(2))
            if less_than:
                counters = 0
        if context is not None:
            match = re.search(r"Bank (\d)\s+\d+\s+([<])*\s(\d+)\/sec", line)
            if match is not None:
                bank = int(match.group(1))
                less_than = match.group(2)
                rate = int(match.group(3))
                if less_than:
                    rate = 0
                if context == "rldram read":
                    rldram_reads[controller][8] += rate
                    rldram_reads[controller][bank] = rate
                elif context == "rldram write":
                    rldram_writes[controller][8] += rate
                    rldram_writes[controller][bank] = rate
                    rldram_total[controller][bank] = (
                        rldram_reads[controller][bank] + rldram_writes[controller][bank]
                    )
                    if rldram_total[controller][bank] > peak:
                        peak = rldram_total[controller][bank]
                elif context == "ddr read":
                    ddr_reads[controller][8] += rate
                    ddr_reads[controller][bank] = rate
                elif context == "ddr write":
                    ddr_writes[controller][8] += rate
                    ddr_writes[controller][bank] = rate
                    ddr_total[controller][bank] = (
                        ddr_reads[controller][bank] + ddr_writes[controller][bank]
                    )
                    if ddr_total[controller][bank] > peak:
                        peak = ddr_total[controller][bank]
            elif re.match(r"^\s*$", line):
                if context == "rldram write" or context == "ddr write":
                    controller += 1
                    for section in rldram_ddr_sections:
                        section[controller] = dict()
                        section[controller][8] = int()
        if re.search(r"LUCHIP\(\d+\) RLDRA.*READ Counts", line):
            if reset_controller:
                controller = 0
                reset_controller = False
            context = "rldram read"
        elif re.search(r"LUCHIP\(\d+\) RLDRA.*WRITE Counts", line):
            context = "rldram write"
        elif re.search(r"LU\(*\d+\)* DDR.*READ Counts", line):
            context = "ddr read"
        elif re.search(r"LU\(*\d+\)* DDR.*WRITE Counts", line):
            context = "ddr write"

    print(
        "\nEDMEM Cache Efficiency (maybe 5% error)\n"
        "=======================================\n"
        "\n                       EMC       RLDRAM    Cache\n"
        "  Controller Access pre-cache  post-cache  Effic.\n"
        "  ---------- ------ ---------- ---------- -------"
    )

    # print(
    #    "rldram_reads = {}, rldram_writes = {}, rldram_total = {}".format(
    #        rldram_reads, rldram_writes, rldram_total
    #    )
    # )
    # print(
    #    "ddr_reads = {}, ddr_writes = {}, ddr_total = {}".format(
    #        ddr_reads, ddr_writes, ddr_total
    #    )
    # )
    # print(
    #    "emc_reads = {}, emc_writes = {}, emc_total = {}".format(
    #        emc_reads, emc_writes, emc_total
    #    )
    # )

    controller = 0
    while controller < 4:
        rldram_total[controller][8] = (
            rldram_reads[controller][8] + rldram_writes[controller][8]
        )
        if emc_reads[controller]:
            print(
                "  {:>10d} read   {:>10d} {:>10d} {:>6.2f}%".format(
                    controller,
                    emc_reads[controller],
                    rldram_reads[controller][8],
                    (emc_reads[controller] - rldram_reads[controller][8])
                    * 100
                    / emc_reads[controller],
                )
            )
        else:
            print(
                "  {:>10d} read   {:>10d} {:>10d}    N/A".format(
                    controller, emc_reads[controller], rldram_reads[controller][8]
                )
            )

        if emc_writes[controller]:
            print(
                "  {:>10s} write  {:>10d} {:>10d} {:>6.2f}%".format(
                    "",
                    emc_writes[controller],
                    rldram_writes[controller][8],
                    (emc_writes[controller] - rldram_writes[controller][8])
                    * 100
                    / emc_writes[controller],
                )
            )
        else:
            print(
                "  {:>10s} write  {:>10d} {:>10d}    N/A".format(
                    "", emc_writes[controller], rldram_writes[controller][8]
                )
            )

        if emc_total[controller]:
            print(
                "  {:>10s} total  {:>10d} {:>10d} {:>6.2f}%".format(
                    "",
                    emc_total[controller],
                    rldram_total[controller][8],
                    (emc_total[controller] - rldram_total[controller][8])
                    * 100
                    / emc_total[controller],
                )
            )
        else:
            print(
                "  {:>10s} total  {:>10d} {:>10d}    N/A".format(
                    "", emc_total[controller], rldram_total[controller][8]
                )
            )

        controller += 1

    print(
        "\nEDMEM Bank Utilization (post-cache, max 533M/8 per second per controller bank)\n"
        "==============================================================================\n"
        "\n  Controller Bank    Reads/s   Writes/s    Total/s Utilization\n"
        "  ---------- ---- ---------- ---------- ---------- -----------"
    )
    controller = 0
    while controller < 4:
        bank = 0
        while bank < 8:
            print(
                "  {:>10d} {:>4d} {:>10d} {:>10d} {:>10d} {:>10.2f}%".format(
                    controller,
                    bank,
                    rldram_reads[controller][bank],
                    rldram_writes[controller][bank],
                    rldram_total[controller][bank],
                    rldram_total[controller][bank] * 100 / (533000000 / 8),
                )
            )
            bank += 1
        controller += 1
    print("\n  Peak {:>6.2f}%\n".format(peak * 100 / (533000000 / 8)))
    print(
        "\nIDMEM Bandwidth (uncached, max 800M/s per controller)\n"
        "=====================================================\n"
        "\n  Controller    Reads/s   Writes/s    Total/s Utilization\n"
        "  ---------- ---------- ---------- ---------- -----------\n"
    )
    peak = 0
    controller = 0
    while controller < 4:
        if imc_total[controller] > peak:
            peak = imc_total[controller]
        print(
            "  {:>10d} {:>10d} {:>10d} {:>10d} {:>10.2f}%".format(
                controller,
                imc_reads[controller],
                imc_writes[controller],
                imc_total[controller],
                imc_total[controller] * 100 / 800000000,
            )
        )
        controller += 1
    print(
        "\n  Peak {:>6.2f}%\n"
        "\nPolicer and Counter Bandwidth\n=============================\n"
        "\n  Policer transactions:  {:>14.14s} ({:>3.0f}% of 200M/s)\n"
        "  Counter transactions:  {:>14.14s} ({:>3.0f}% of 400M/s)\n".format(
            peak * 100 / 800000000,
            commify(policers),
            (policers * 100) / 200000000,
            commify(counters),
            (counters * 100) / 400000000,
        )
    )

    total = 0
    limit = 80 * 10
    cmd = "bringup jspec read luchip[{}] register hash min_num_pipe_id".format(lu)
    for loop in range(0, 10):
        exit_code, result = pfe_command(slot, slot_str, cmd)
        if exit_code:
            lines = result
        else:
            print("ERROR :: unable to get output from cmd '{}'".format(cmd))
            sys.exit(1)
        for line in lines:
            match = re.match(
                r"0x[0-9a-fA-F]+\s+lu\.hash\.min_num_pipe_id\s+([0-9a-fA-F]+)", line
            )
            try:
                total += int("0x{}".format(match.group(1)), 16)
            except:
                pass
    print(
        "\nHash Utilization\n================\n"
        "\n  Hash utilization: {:3d} ({:3.0f}% of 800 opportunities)\n"
        "\nParcel Metrics\n==============\n"
        "\n  Parcels per second:              {:>14.14s}\n"
        "  Average instructions per parcel: {:>14.0f}\n"
        "  Average waits per parcel:        {:>14.0f}\n"
        "  Average cycles per parcel:       {:>14.0f}".format(
            limit - total,
            (limit - total) * 100 / limit,
            commify(total_parcels),
            total_inst / total_parcels,
            total_wait / total_parcels,
            (total_inst + total_wait) / total_parcels,
        )
    )

    controller = 0
    total_idmem_reads = 0
    total_idmem_writes = 0
    total_edmem_reads = 0
    total_edmem_writes = 0
    while controller < 4:
        total_idmem_reads += imc_reads[controller]
        total_idmem_writes += imc_writes[controller]
        total_edmem_reads += emc_reads[controller]
        total_edmem_writes += emc_writes[controller]
        controller += 1

    print(
        "\n                                IDMEM    EDMEM    Total\n"
        "  Average reads/parcel:      {:>8.2f} {:>8.2f} {:>8.2f}\n"
        "  Average writes/parcel:     {:>8.2f} {:>8.2f} {:>8.2f}\n"
        "  Average accesses/parcel:   {:>8.2f} {:>8.2f} {:>8.2f}\n".format(
            total_idmem_reads / total_parcels,
            total_edmem_reads / total_parcels,
            (total_idmem_reads + total_edmem_reads) / total_parcels,
            total_idmem_writes / total_parcels,
            total_edmem_writes / total_parcels,
            (total_idmem_writes + total_edmem_writes) / total_parcels,
            (total_idmem_reads + total_idmem_writes) / total_parcels,
            (total_edmem_reads + total_edmem_writes) / total_parcels,
            (
                total_idmem_reads
                + total_edmem_reads
                + total_idmem_writes
                + total_edmem_writes
            )
            / total_parcels,
        )
    )


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
    if "." in n:
        dollars, cents = n.split(".")
    else:
        dollars, cents = n, None

    r = []
    for i, c in enumerate(str(dollars)[::-1]):
        if i and (not i % 3):
            r.insert(0, ",")
        r.insert(0, c)
    out = "".join(r)
    if cents:
        out += "." + cents
    return out


def countbits(number):
    """ countbits -count number of ones
    """
    count = 0

    for bit in range(0, 32):
        if number & (1 << bit):
            count = count + 1

    return count


def main(slot, slot_str, lu):
    """ main event
    """
    print(
        "\n-----------------------------------LU {}"
        "---------------------------------------".format(lu)
    )
    issue_commands(slot, slot_str, lu)
    process_results(slot, slot_str, lu)


if __name__ == "__main__":

    debug = False
    slot = None
    pfe = None
    print("Script Version # {}".format(version))

    # Parse the arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:p:d:h", [])
    except getopt.GetoptError:
        print(
            "ERROR :: Seems to be an error with input arguments. Please check usage below"
        )
        usage()
    for opt, arg in opts:
        if opt == "-h":
            usage()
        elif opt in "-s":
            slot = int(arg)
        elif opt in "-p":
            pfe = int(arg)
        elif opt in "-d":
            debug = bool(arg)

    cmd = "sysctl hw.product.router_max_fpc_slots"
    exit_code, result = shell_command(cmd)
    if exit_code:
        max_fpc_slots = int(result[0].split()[1])
    else:
        print("ERROR :: unable to determine number of fpc slots")
        sys.exit(1)

    if slot < 0 or slot >= max_fpc_slots:
        print("ERROR :: slot number missing or invalid")
        usage()

    cmd = "sysctl hw.product.router_max_lcc_slots"
    exit_code, result = shell_command(cmd)
    if exit_code:
        max_lcc_slots = int(result[0].split()[1])
    else:
        print("ERROR :: unable to determine number of lcc slots")
        sys.exit(1)

    cmd = "sysctl net.tnp.tnp_chassis_id"
    exit_code, result = shell_command(cmd)
    if exit_code:
        chassis_id = int(result[0].split()[1])
    else:
        print("ERROR :: unable to determine number of lcc chassis id")
        sys.exit(1)

    if chassis_id:
        if slot < (max_fpc_slots / max_lcc_slots):
            slot_str = "member{}-fpc{}".format("0", slot)
            cmd = "cli -c 'show chassis hardware member {} | grep \"FPC {} \"'".format(
                "0", slot
            )
        else:
            slot_str = "member{}-fpc{}".format(
                "1", slot - int(max_fpc_slots / max_lcc_slots)
            )
            cmd = "cli -c 'show chassis hardware member {} | grep \"FPC {} \"'".format(
                "1", slot - int(max_fpc_slots / max_lcc_slots)
            )
    else:
        cmd = "sysctl hw.product.model"
        exit_code, result = shell_command(cmd)
        if exit_code:
            model = result[0].split()[1]
        else:
            print("ERROR :: unable to determine router model")
            sys.exit(1)

        if re.match(r"mx80$|mx80\-|mx40\-|mx10\-|mx5\-", model):
            fpc_str = "tfeb"
            slot = 0
        elif re.match(r"mx104$", model):
            fpc_str = "afeb"
            slot = 0
        else:
            fpc_str = "fpc"

        slot_str = "{}{}".format(fpc_str, slot)
        cmd = "cli -c 'show chassis hardware' | grep 'FPC {} '".format(slot)

    print(
        "-------------------------Getting linecard information-------------------------"
    )
    exit_code, result = shell_command(cmd)
    if exit_code:
        fpc_model = result[0].split()
        if len(fpc_model) == 6:
            fpc_model = " ".join(fpc_model[4:])
        else:
            fpc_model = " ".join(fpc_model[6:])
        print("\n{}".format(result[0]))
    else:
        print("ERROR :: fpc slot is likely empty")
        usage()

    mpc_lookup = {
        "MPC Type 1": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 1 3D": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC Type 1 3D Q": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 1 3D Q": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200 40x1G Copper": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200-40x1G-SFP": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200-40FE": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "BUILTIN": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC BUILTIN": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MS-MPC": {
            "num pfe": 1,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC Type 2 3D": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC Type 2 3D Q": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC Type 2 3D EQ": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 2 3D": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 2 3D Q": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 2 3D EQ": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPCE Type 2 3D P": {
            "num pfe": 2,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC 3D 16x 10GE": {
            "num pfe": 4,
            "pfe 0 lu index": [0],
            "pfe 1 lu index": [1],
            "pfe 2 lu index": [2],
            "pfe 3 lu index": [3],
        },
        "MPCE Type 3 3D": {
            "num pfe": 1,
            "pfe 0 lu index": [0, 4, 8, 12],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200 4x40G QSFP": {
            "num pfe": 1,
            "pfe 0 lu index": [0, 4, 8, 12],
            "pfe 1 lu index": None,
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC4E 3D 32XGE": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4],
            "pfe 1 lu index": [1, 5],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "MPC4E 3D 2CGE+8XGE": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4],
            "pfe 1 lu index": [1, 5],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200 32x10G SFP": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4],
            "pfe 1 lu index": [1, 5],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "EX9200-2C-8XS": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4],
            "pfe 1 lu index": [1, 5],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "FPC Type 5-3D": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4, 8],
            "pfe 1 lu index": [1, 5, 9],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
        "FPC Type 5-LSR": {
            "num pfe": 2,
            "pfe 0 lu index": [0, 4, 8],
            "pfe 1 lu index": [1, 5, 9],
            "pfe 2 lu index": None,
            "pfe 3 lu index": None,
        },
    }

    try:
        num_pfe = mpc_lookup[fpc_model]["num pfe"]
    except KeyError:
        print("ERROR :: FPC type '{}' not LU based".format(fpc_model))
        sys.exit(1)

    if pfe < 0 or pfe >= num_pfe:
        print("ERROR :: PFE number missing or invalid")
        usage()

    cmd_output = []
    lu_clk_freq = 800000000
    sample = 100
    ppe_avg_util = 0
    for lu in mpc_lookup[fpc_model]["pfe {} lu index".format(pfe)]:
        main(slot, slot_str, lu)
