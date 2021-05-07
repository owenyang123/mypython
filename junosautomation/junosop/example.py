from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell
from datetime import datetime as t
# from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
import re
 
try:
        os.mkdir("/var/tmp/script_outputs")
except:
        print('Script Directory already existed')
 
Date = t.today().strftime("%Y%m%d%H%M%S")
# Path = os.getcwd() + "/{}/".format(Date)
Path = "/var/tmp/script_outputs/{}/".format(Date)
print(Path)
# os.mkdir(Path)
try:
        os.mkdir(Path)
except:
        print('Directory already existed')
 
                                        
class ERO_Trace(object):
        def __init__(self, ERO):
                self.ERO = ERO
                print "start"
                command = 'cli show configuration protocols bgp group iBGP \| match local-address'
                self.fqdn = os.popen(command).read()[14:-2]
                RSVP_SESSION_NEIGHBOR = os.popen(
                        'cli show configuration protocols mpls label-switched-path {} \| match to'.format(
                                self.ERO)).read()[3:-2]
                self.RSVP_SESSION_NEIGHBOR = RSVP_SESSION_NEIGHBOR
                command = "cli show route receive-protocol bgp {} \| match '\*'".format(RSVP_SESSION_NEIGHBOR)
                try:
                        dest = os.popen(command).read().splitlines()[0]
                        Destination_IP = dest[2:dest.find('/')]
                except:
                        Destination_IP = RSVP_SESSION_NEIGHBOR
                self.Destination_IP = Destination_IP
                                        
                LSP_List = set({})
                Next_Hop_List = set({})
                command = 'cli show route {}'.format(Destination_IP)
                route = os.popen(command).read()
                self.document_InTextfile(command, route)
                for x in route.splitlines():
                        if '-00' in x:
                                LSP_List.add(x.split(' ')[-1])
                                Next_Hop_List.add(x.split(' ')[-5])
 
                Next_Hop_List = list(Next_Hop_List)
                # LSP = list(LSP_List)[0]
 
                RRO_LIST = []
                command = 'cli show mpls lsp extensive name {} \| no-more'.format(self.ERO)
                RRO = os.popen(command).read()
                self.document_InTextfile(command, RRO)
                for x in RRO.splitlines():
                        if " S " in x: RRO_LIST.append(x)
 
                Unilist_List = []       
                command = 'cli show route forwarding-table destination {} table default'.format(Destination_IP)
                Forwarding = os.popen(command).read()
                self.document_InTextfile(command, Forwarding)
                for x in Forwarding.splitlines():
                        if 'ulst' in x: Unilist_List.append(int(x.split(' ')[x.split(' ').index('ulst') + 2]))
                        if 'comp' in x: Unilist_List.append(int(x.split(' ')[x.split(' ').index('comp') + 6]))
 
                Label_Out_List = [0, 0]
                command = 'cli show rsvp session detail name {} \| no-more'.format(self.ERO)
                RSVP_Session = os.popen(command).read()
                self.document_InTextfile(command, RSVP_Session)
                for RSVP_Session1 in RSVP_Session.split(RSVP_SESSION_NEIGHBOR):
                        if "LSPpath: Secondary" in RSVP_Session1:
                                index = 1
                        if "LSPpath: Primary" in RSVP_Session1:
                                index = 0
                        for x in RSVP_Session1.splitlines():
                                if "Label out:" in x: Label_Out_List[index] = int(x.split(' ')[-1])
 
                FPC_LIST = []
                command = 'cli show chassis hardware models \| no-more'
                FPC = os.popen(command).read()
                self.document_InTextfile(command, FPC)
                for x in FPC.splitlines():
                        if 'show' not in x and 'FPC' in x: FPC_LIST.append(x.split('    ')[0])
 
                for Unilist in Unilist_List:
                        for FPC in FPC_LIST:
                                self.document_InTextfile(command, os.popen(
                                        'cprod -A {} -c "show nhdb id {} extensive"'.format(
                                                str(FPC).replace('FPC ', 'fpc'), Unilist)).read())
 
                command = 'ping -c 5 {}'.format(Destination_IP)
                PING = os.popen(command).read()
                self.document_InTextfile(command, PING)
                                        
                # TRACEROUTE = os.popen('traceroute {}'.format(Destination_IP), this=None)[1]
                # self.document_InTextfile(command,TRACEROUTE)
 
                for x in range(0, len(Next_Hop_List)):
                        data = "---> Starting trace for nexthop {} from ingress LSR".format(x)
                        self.document_InTextfile(command, data)
                        fqdn = Next_Hop_List[x]
                        Label_Out = Label_Out_List[x]
                        while Label_Out != 3:
                                print("{}, {}".format(fqdn, Label_Out))
                                fqdn, Label_Out = self.Collect_Data(fqdn, Label_Out)
 
        def document_InTextfile(self, command, Data):
                try:
                        with open(Path + self.ERO + '.txt', 'a') as file:
                                file.write(self.fqdn + " :----->" + command + '\n' + Data + '\n\n\n')
                except:
                        print(self.ERO + ": " + self.fqdn + " :----->\n" + Data)
                        print('**Failed to create text file output for {}'.format(self.ERO))
 
        def Collect_Data(self, fqdn, Label_Out):
                self.fqdn = fqdn
                print("Conecting to {}".format(fqdn))
                ss = StartShell(Device(host=fqdn, user='junisp', passwd='c5%!4yAa'))
                ss.open()
 
                LSP_List = []
                Next_Hop_List = []
                # print ("before route")
                command = 'cli show route label {}'.format(Label_Out)
                route = ss.run(command, this=None, timeout=5)[1]
                # print ("after route")
                self.document_InTextfile(command, route)
                # print ("after self.document_InTextfile")
                print("route: ", route)
                for x in route.splitlines():
                        if '-00' in x:
                                LSP_List.append(x.split(' ')[-1])
                                Next_Hop_List.append(x.split(' ')[-5])
                                        
                LSP = LSP_List[0]
 
                RRO_LIST = []
                command = 'cli show mpls lsp extensive name {} \| no-more'.format(LSP)
                RRO = ss.run(command, this=None, timeout=5)[1]
                self.document_InTextfile(command, RRO)
                for x in RRO.splitlines():
                        if " S " in x: RRO_LIST.append(x)
 
                Unilist_List = []
                command = 'cli show route forwarding-table label {} table default'.format(Label_Out)
                Forwarding = ss.run(command, this=None, timeout=5)[1]
                self.document_InTextfile(command, Forwarding)
                for x in Forwarding.splitlines():
                        if 'ulst' in x: Unilist_List.append(int(x.split(' ')[x.split(' ').index('ulst') + 2]))
                        if 'comp' in x: Unilist_List.append(int(re.search("comp\s+(\d+)", x).group(1)))
 
                Label_Out_List = [None, None]
                command = 'cli show rsvp session detail name {} \| no-more'.format(self.ERO)
                RSVP_Session = ss.run(command, this=None, timeout=5)[1]
                self.document_InTextfile(command, RSVP_Session)
                for RSVP_Session1 in RSVP_Session.split(self.RSVP_SESSION_NEIGHBOR):
                        if "LSPpath: Secondary" in RSVP_Session1:
                                index = 1
                        if "LSPpath: Primary" in RSVP_Session1:
                                index = 0
                        for x in RSVP_Session1.splitlines():
                                if "Label out:" in x: Label_Out_List[index] = int(x.split(' ')[-1])
 
                FPC_LIST = []
                command = 'cli show chassis hardware models \| no-more'
                FPC = ss.run(command, this=None, timeout=5)[1]
                self.document_InTextfile(command, FPC)
                for x in FPC.splitlines():
                        if 'show' not in x and 'FPC' in x: FPC_LIST.append(x.split('    ')[0])
 
                for Unilist in Unilist_List:
                        print Unilist   
                        for FPC in FPC_LIST:
                                print FPC
                                command = 'cprod -A {} -c "show nhdb id {} extensive"'.format(
                                        str(FPC).replace('FPC ', 'fpc'), Unilist)
                                self.document_InTextfile(command, ss.run(command, this=None, timeout=5)[1])
                FPC_LIST = []
 
                PING = ss.run('ping -c 5 {}'.format(self.Destination_IP), this=None, timeout=5)[1]
                self.document_InTextfile(command, PING)
 
                # TRACEROUTE = ss.run('traceroute {}'.format(Destination_IP), this=None)[1]
                # self.document_InTextfile(command,TRACEROUTE)
 
                ss.close()
                for Label_Out in Label_Out_List:
                        if Label_Out is not None:
                                return Next_Hop_List[0], Label_Out
                                        
 
if __name__ == '__main__':
        # Screen_Length = os.popen('cli set cli screen-length 0; cli set cli screen-width 0').read()
        log = os.popen('cli show log messages \| match RPD_MPLS_PATH_DOWN').read()
        ERO_List = set({})
        for line in log.splitlines():
                ERO_List.add([j for j in line.split() if j!=""][-1])
        ERO_List = list(ERO_List)
        print "ERO_List = {}".format(ERO_List)
 
 
        def fun(x):
                print("inside worker {}".format(x))
 
        if ERO_List!=[]:
                for ERO in ERO_List:
                        ERO_Trace(ERO)
 
        else:print "Empty list"
        print "done"
        # with ProcessPoolExecutor(len(ERO_List)) as ex:
        # res = ex.map(ERO_Trace, ERO_List)
        # res = ex.map(fun, ERO_List)
