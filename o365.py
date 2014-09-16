#! /usr/bin/python

'''
This script parses Microsoft's o365 IP webpage and updates a specific
object-group in a Cisco ASA with the new IP addreses. It can also
remove IPs, but that functionality is commented out.
'''

import re 
import paramiko
import requests
import os
import datetime
import time
import netaddr
import creds

################################
####### Custom Variables #######
################################
### Set MS url
url = "http://technet.microsoft.com/en-us/library/hh373144.aspx"

### Set device IPs
devices = ["192.168.25.254"]

### Set o365 object-group
object_group = "MS-OFFICE365-SUBNETS"

### Set device username and password - or remove user and pass variables and change the "account" variable to "read_login()" to ask for password at script run - no automation.
username = creds.username
password = creds.password
enable_pw = creds.enable_pw

date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

#### Functions ####
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
	
	with open("new-ip-list.txt", "w+") as out_file:
		for ip in ip_list:
			out_file.writelines(ip + "\n")
	
	configure(devices)

def enable(conn, enable_pw):
	conn.send("enable\r")
	time.sleep(1)
	conn.send(enable_pw + "\r")
	time.sleep(1)

def compare():
	commands = ["object-group network " + object_group,]
	old = [line.rstrip() for line in open("old-ip-list.txt", "r").readlines()]
	new = [line.rstrip() for line in open("new-ip-list.txt", "r").readlines()]
	for ip in new:
		if ip in old:
			pass
		if ip not in old:
			ip = netaddr.IPNetwork(ip)
			commands.append(" network-object {} {}".format(str(ip.ip), str(ip.netmask)))
	for ip in old:
		if ip not in new and "/" in ip:
			ip = netaddr.IPNetwork(ip)
			print("------ {} appears to have been removed from MS IP list ------".format(str(ip.cidr)))
			with open("removed-ip." + date + ".txt", "a") as out_file:
				out_file.writelines(ip + "\n")
			# commands.append(" no network-object " + ip)
	return commands

def configure(devices):
	commands = compare()
	if len(commands) > 1:
		for device in devices:
			try:
				output = []
				conn_pre = paramiko.SSHClient()
				conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				conn_pre.connect(device, username=username, password=password)
				conn = conn_pre.invoke_shell()
				time.sleep(1)
				if ">" in conn.recv(100000):
					enable(conn, enable_pw)
					time.sleep(0.5)
				print("\n====== Configuring {} ======".format(device))
				conn.send("conf t\r")
				time.sleep(1)

				for command in commands:
					conn.send(command + "\r")
					time.sleep(0.5)

				output.append(conn.recv(100000))

				with open(device + "_" + date + ".out", "a") as out_file:
					out_file.writelines(output)
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