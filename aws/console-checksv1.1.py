#!/apollo/sbin/envroot "$ENVROOT/python3.6/bin/python3.6"

##################################################Function to extract everything else from output####################################################
def all_commands_running():
    with open('command_file.txt') as infile:
        x = infile.read()
        x = x.splitlines()
        return x

x = all_commands_running()
#print(all_commands_running())

def other_commands_in_list():
    other_commands_list = []
    for items in x:
        if (items != 'show bgp summary' and items != 'show version'):
            other_commands_list.append(items + " ")
    return other_commands_list

all_other_commands = other_commands_in_list()
#print(all_other_commands)

def extract_everything_else():
    with open('log.txt') as infile:
        x = infile.read()
        y = x.split('\n')
        copy = 0
        output_everything_else = []
        #print(y)
    for count,items in enumerate(y):
        a = count + 1
    #print(a)
    for i, line in enumerate(y):

            if y[i] in all_other_commands:
                copy = a
                while (copy == a):
                    if (y[i] == "show version " or y[i] == 'show bgp summary '):
                        break
                    else:
                        output_everything_else.append(y[i])
                        i = i + 1
                        if (i == a or y[i] in all_other_commands):
                            break


    return output_everything_else

#print(extract_everything_else())
for eachline in extract_everything_else():
  print(eachline)


##################################################Function to extract only show bgp summary output####################################################

def extract_show_bgp_summary_lines():
    with open('log.txt') as infile:
        x = infile.read()
    copy = 0
    output_bgp_summary = []
    y = x.split('\n')
    #print(y)
    for i, line in enumerate(y):
        if line == "show bgp summary ":
            i = i+1
            line = output_bgp_summary.append(y[i])

            while (copy == 0):
                if y[i] == "BGP is not running":
                  break
                if y[i] != "BGP is not running":
                  i = i + 1
                  output_bgp_summary.append(y[i])

                  if y[i] == '  MAINTENANCE.inet.0: 0/0/0/0':
                     copy = 1
                     break

    return output_bgp_summary
#print(extract_show_bgp_summary_lines())

##################################################Function to extract only show version output from the cli_output file####################################################
def extract_show_version_lines():
    with open('log.txt') as infile:
        x = infile.read()

    copy = 0
    output_version = []
    y = x.split('\n')
    #print(y)

    for i, line in enumerate(y):
        if line == "show version ":
            
           print(y[i])

           while (copy == 0):
                i = i + 1
                output_version.append(y[i])

                if y[i] == 'Junos for Automation Enhancement':
                    copy = 1  #
                    break

    return output_version
#
#################################################Conditional to match 'our show version list' with standard show version output###############################################
for eachline in extract_show_version_lines():

     if (eachline[0:5] != 'JUNOS' and eachline[0:5] != 'Junos'):
        #print(eachline)
         continue

     elif (eachline == 'Junos: 14.1X53-D28.17' or eachline == 'JUNOS Base OS Software Suite [14.1X53-D28.17]' or eachline == 'JUNOS Base OS boot [14.1X53-D28.17]' or eachline == 'JUNOS Crypto Software Suite [14.1X53-D28.17]' or eachline == 'JUNOS Online Documentation [14.1X53-D28.17]' or eachline == 'JUNOS Kernel Software Suite [14.1X53-D28.17]' or eachline == 'JUNOS Packet Forwarding Engine Support (qfx-ex-x86-32) [14.1X53-D28.17]' or eachline == 'JUNOS Routing Software Suite [14.1X53-D28.17]' or eachline == 'JUNOS Enterprise Software Suite [14.1X53-D28.17]' or eachline == 'JUNOS py-base-i386 [14.1X53-D28.17]' or eachline == 'JUNOS py-extensions-i386 [14.1X53-D28.17]' or eachline == 'JUNOS Host Software [14.1X53-D28.17]' or eachline == 'Junos for Automation Enhancement') :
       
        print(eachline)

     else:
         print ("{eachline}".format(eachline = "\x1b[3;31;40m" + eachline + "\x1b[0m"))


##################################################Conditional to match 'our show bgp summary list' with standard show bgp output and printing output accordingly###############################################

bgp_list = extract_show_bgp_summary_lines()
#print(bgp_list)
if bgp_list[0] == 'BGP is not running':
    print('\nshow bgp summary\n' + bgp_list[0])
else:
    bgp_list_check = bgp_list[0].split('Peers: 2')
    #print(bgp_list_check)
    if bgp_list_check[1] !=  ' Down peers: 0':
        print('\nshow bgp summary')
        for eachline in bgp_list:
            print ("{eachline}".format(eachline = "\x1b[3;31;40m" + eachline + "\x1b[0m"))
    else:
        print('\nshow bgp summary')
        for eachline in bgp_list:
            print(eachline)


