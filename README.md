o365
======

# Description:
This script parses Microsoft's Office 365 IP webpage (http://technet.microsoft.com/en-us/library/hh373144.aspx) 
and updates a specific object-group in a Cisco ASA with the new IP addreses. 
It can also remove IPs, but that functionality is commented out.

# Usage:
<pre>
#./o365.py 

###############################################################################################
Microsoft URL: http://technet.microsoft.com/en-us/library/hh373144.aspx
User Account: colby-test
Devices: 192.168.14.2, 192.168.14.1, 1.1.1.1, 192.168.14.2
Object Group: MS-OFFICE365-SUBNETS
###############################################################################################

====== Configuring 192.168.14.2 ======

====== Configuration applied successfully, output file '192.168.14.2_2014-07-12_23-38.out' was created ======

====== Configuring 192.168.14.1 ======

!!!!!! ------ There was an issue with 192.168.14.1, see file: '192.168.14.1_2014-07-12_23-38.error.out' ------ !!!!!!

!!!!!! ------ There was an issue with 1.1.1.1, see file: '1.1.1.1_2014-07-12_23-38.error.out' ------ !!!!!!
</pre>