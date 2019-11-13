python
====== 

python scripts repository


PYTHON Scripts List:
--------------------
submodule: pypuller

1. <LSPcreator.py> is a script used to create a variable amount of LSPs.

2. <ttrace_prep.py> is for getting outputs needed to capture packet on customer router from lookup process.

3. <hexify.py> is for converting IPv4 addresses to IPv6 addresses (and vice versa), typically for usage with <ttrace_prep.py>

4. <mail_message.py> is called in other scripts to send an email.

5. <check_status.py> is useful for recalling how to pull certain data from the box.

6. <mgd-apply-config.py> is for looping application and removal of configs (in private mode), created from a .j2 template, with a different UUID for each run 		on a MX device. Specifies a present MS-MPC and VT interface.

7. <test-ssh.py> is used to test SSH functionality on a Junos device based on its IPv4 address.

8. <config_set_rollback_loop.py> is used to add config and perform rollback loop from remote server continously.
	Server req: Python/PyEZ
	Device req: Netconf over SSH

9. <interface_flap_template.py> is used to flap interfaces from remote server.
	Server req: Python/PyEZ
	Device req: Netconf over SSH

10. <Cluster_Checks.py> is used to generate a text file containing information about a cluster.

11. <Hardware_Checks.py> is used to generate a text file containing information about a chassis.

12. <jnpr_cpu_mon.py> is used to determine root cause of high CPU usage in Junos device.

13. <render_config.py> is used to create large numbers of IPSec peers.

14. charter-vmcore.py>is used to perform routing-engine mastership switchovers, and check for certain conditions such as occurrences of core files and system uptime. This is meant to perform multiple iterations with intention of re-creating an issue seen by the customer in the production. **Currently in development**