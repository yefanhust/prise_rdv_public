#!/usr/bin/env python

import os, time, datetime, modules
from os import path

ts = time.time()
stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
p = raw_input("Priority(Highest priority:0, Default:9)> ")
if p=='':
    p=9
firstname = raw_input("Firstname> ")
lastname = raw_input("Lastname> ")
email=raw_input("Email(default value=your-own-email-address> ")
emailcheck=raw_input("Email check>")
while email!=emailcheck:
    email=raw_input("Email(default value=your-own-email-address)> ")
    emailcheck=raw_input("Email check>")
number_agdref = raw_input("number_agdref> ")
end_date_validity = raw_input("end_date_validity(JJ/MM/AAAA)> ")
post_code = raw_input("post_code> ")
last_tol = raw_input("last_tolerated_date(JJ/MM/AAAA, default:31/12/9999)> ")

if email=="":
    email="your-own-email-address"
    emailcheck="your-own-email-address"
if last_tol=="":
    last_tol="31/12/9999"


dirname = modules.makeDir("queued")
filename = path.join(dirname, str(p)+str(stamp)+".txt")
lines="firstname="+firstname+"\n"+"lastname="+lastname+"\n"+"email="+email+"\n"+"emailcheck="+emailcheck+"\n"+"number_agdref="+number_agdref+"\n"+"end_date_validity="+end_date_validity+"\n"+"post_code="+post_code+"\n"+"last_tolerated_date="+last_tol+"\n"

with open(filename, "w") as newClientTXT:
    newClientTXT.write("%s" % lines)
