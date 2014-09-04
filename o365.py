#! /usr/bin/python

'''
This script parses Microsoft's o365 IP webpage and updates a specific
object-group in a Cisco ASA with the new IP addreses. It can also
remove IPs, but that functionality is commented out.
'''

import re
import sys
### Need Exscript installed - pip install https://github.com/knipknap/exscript/tarball/master
from Exscript.util.interact import read_login
import Exscript
### Need requests installed - pip install requests
import requests
import os
import datetime
import creds

################################
####### Custom Variables #######
################################
### Set MS url
url = "http://technet.microsoft.com/en-us/library/hh373144.aspx"

### Set device IPs
devices = ["192.168.14.2", "192.168.14.1", "1.1.1.1", "192.168.14.2"]

### Set o365 object-group
object_group = "MS-OFFICE365-SUBNETS"

### Set device username and password - or remove user and pass variables and change the "account" variable to "read_login()" to ask for password at script run - no automation.
username = creds.username
password = creds.password
account = Exscript.Account(username, password)
# account = read_login()

date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

### Functions ###
def main():
	print("\n" + "#" * 95)
	print("Microsoft URL: {}".format(url))
	print("User Account: {}".format(username))
	print("Devices: {}".format(", ".join(devices)))
	print("Object Group: {}".format(object_group))
	print("#" * 95)

	page = requests.get(url)
	content = page.content
	
	ip_list = re.findall('(?:[0-9]{1,3}\.){3}[0-9]{1,3}\/[0-3][0-9]|(?:[0-9]{1,3}\.){3}[0-9]{1,3}', content)

	if "new-ip-list.txt" in os.listdir("./"):
		os.rename("new-ip-list.txt", "old-ip-list.txt")
	else:
		open("old-ip-list.txt", "w+").close()
				
	new = open("new-ip-list.txt", "w+")
	for ip in ip_list:
		new.writelines(ip + "\n")
	new.close()
	
	configure(devices, account)

def cidr2dotmask(ip):
	mask_dict = {'/16': ' 255.255.0.0', 
				'/17': ' 255.255.128.0', 
				'/18': ' 255.255.192.0', 
				'/19': ' 255.255.224.0', 
				'/20': ' 255.255.240.0', 
				'/21': ' 255.255.248.0', 
				'/22': ' 255.255.252.0', 
				'/23': ' 255.255.254.0', 
				'/24': ' 255.255.255.0', 
				'/25': ' 255.255.255.128', 
				'/26': ' 255.255.255.192', 
				'/27': ' 255.255.255.224', 
				'/28': ' 255.255.255.240', 
				'/29': ' 255.255.255.248', 
				'/30': ' 255.255.255.252', 
				'/31': ' 255.255.255.254', 
				'/32': ' 255.255.255.255'}
	for key in mask_dict.keys():
		if key in ip:
			mask = re.sub(key, mask_dict[key], ip.rstrip())
	return mask

def compare():
	commands = ["object-group network " + object_group,]
	old = [line.rstrip() for line in open("old-ip-list.txt", "r").readlines()]
	new = [line.rstrip() for line in open("new-ip-list.txt", "r").readlines()]
	for ip in new:
		if ip in old:
			pass
		if ip not in old and "/" in ip:
			ip = cidr2dotmask(ip)
			commands.append(" network-object " + ip)
		elif ip not in old:
			commands.append(" network-object host " + ip)
	for ip in old:
		if ip not in new and "/" in ip:
			ip = cidr2dotmask(ip)
			print("------ {} appears to have been removed from MS IP list ------".format(ip))
			removed = open("removed-ip." + date + ".txt", "a")
			removed.writelines(ip + "\n")
			removed.close()
			# commands.append(" no network-object " + ip)
		elif ip not in new:
			print("------ {} appears to have been removed from MS IP list ------".format(ip))
			# commands.append(" no network-object host " + ip)
			removed = open("removed-ip." + date + ".txt", "a")
			removed.writelines(ip + "\n")
			removed.close()
	return commands

def configure(devices, account):
	conn = Exscript.protocols.SSH2(timeout=2)
	conn.set_driver('ios')
	commands = compare()
	if len(commands) > 1:
		for device in devices:
			try:
				conn.connect(device)
				conn.login(account)
				conn.send("conf t\r")
				print("\n====== Configuring {} ======".format(device))
				for cmd in commands:
					conn.execute(cmd)
					output = conn.response
					out_file = open(device + "_" + date + ".out", "a")
					out_file.writelines(output)
				conn.send('wr\r')
				conn.close()
				print("\n====== Configuration applied successfully, output file '{}_{}.out' was created ======\n".format(device, date))
			except Exception as e:
				print("\n!!!!!! ------ There was an issue with {}, see file: '{}_{}.error.out' ------ !!!!!!\n".format(device, device, date))
				out_file = open(device + "_" + date + ".error.out", "w")
				out_file.writelines(e)
		print("\n")
	else:
		print("\n!!!!!! ------ No changes necessary ------ !!!!!!\n")

if __name__ == "__main__":
	main()