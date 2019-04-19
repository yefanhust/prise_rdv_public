#!/usr/bin/env python

import modules
import os
from os import path


headers = {
'Demande':'POST /booking/create/14056/1 HTTP/1.1',
'Host': 'www.essonne.gouv.fr',
'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Origin': 'http://www.essonne.gouv.fr',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36',
'Content-Type': 'application/x-www-form-urlencoded',
'Referer': 'http://www.essonne.gouv.fr/booking/create/14056/0',
'Accept-Encoding': 'gzip,deflate',
'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4,zh;q=0.2',
}

cookies = dict(xtvrn='$481982$',xtan481982='-',xtant481982='1',eZSESSID='7hg39q6809lm4dd9crnspt9qf5')

m = modules.RdvManager(headers,cookies)

queued_dir = modules.makeDir("queued")
finished_dir = modules.makeDir("finished")
invalidated_dir = modules.makeDir("invalidated")
path_nextclient = modules.scheduler()
# tested with hotmail and gmail
rdvMailAddr={"your-email-address-0":"your-email-password-0",
             "your-email-address-1":"your-email-password-1"}
while(path_nextclient!=""):
    print "Now processing the client: "+path.basename(path_nextclient)
    pInfo = modules.readInfo(path_nextclient)
    if type(pInfo)!=type({}):
        print "Invalid client info."
        with open(path_nextclient, "a") as f:
            if pInfo==0:
                f.write("Invalidate Code: 0 (invalid end date)")
            elif pInfo==1:
                f.write("Invalidate Code: 1 (invalid post code length)")
            elif pInfo==2:
                f.write("Invalidate Code: 2 (invalid agdref number length)")
        os.rename(path_nextclient, path.join(invalidated_dir, path.basename(path_nextclient)))
        path_nextclient = modules.scheduler()
        continue 
    ret = m.grabRdv(pInfo, rdvMailAddr)
    if ret==0:
        with open(path_nextclient, "a") as f:
            f.write("Invalidate Code: 9 (unknown reason)")
        os.rename(path_nextclient, path.join(invalidated_dir, path.basename(path_nextclient)))
    else:
        with open(path_nextclient, "a") as f:
            f.write("Edit the RdV with the link: "+ret+"\n")
            f.write("Remove the RdV with the link: "+ret.replace("confirm","remove"))
        os.rename(path_nextclient, path.join(finished_dir, path.basename(path_nextclient)))
    path_nextclient = modules.scheduler()
print "All dossiers have been processed."
