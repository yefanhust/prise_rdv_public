#!/usr/bin/env python

# -*- coding: latin-1 -*-
import requests
import urllib
import urllib2
import time
import modules 
from os import path
from os import rename
from os import listdir
import shutil

# Have got ride of {'Content-Length': '65',} beneath the {'Connection': 'keep-alive',}
# For it blocks the post request for url_captcha
# It has to be the same headers and cookies 
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

url0 = 'http://www.essonne.gouv.fr/booking/create/14056/0' # Page initiale 
url1 = 'http://www.essonne.gouv.fr/booking/create/14056/1' # Choix de la nature du rdv
url2 = 'http://www.essonne.gouv.fr/booking/create/14056/2' # Pas de disponibilité
url3 = 'http://www.essonne.gouv.fr/booking/create/14056/3' # Description de la nature du rendez-vous
url4 = 'http://www.essonne.gouv.fr/booking/create/14056/4' # Choix d'une plage horaire
url6 = 'http://www.essonne.gouv.fr/booking/create/14056/6' # Côntrole de sécurité (captcha) 
url8 = 'http://www.essonne.gouv.fr/booking/create/14056/8' # Coordonnées personnelles
url9 = 'http://www.essonne.gouv.fr/booking/create/14056/9' # Validation de la demande de rendez-vous

# what url0 needs, however url1 reachable without passing by url0
#data ={
#'condition':'on',
#'nextButton':'Effectuer+une+demande+de+r%C3%A9servation'}
#data = urllib.urlencode(data)

data = {
'planning':'15992',
'nextButton':'Etape+suivante'}
data = urllib.urlencode(data)

req = requests.post(url=url1, data=data, headers=headers, cookies=cookies)
c = 0
while req.url!=url3:
    c += 1
    print c
    try:
        req = requests.post(url=url1, data=data, headers=headers, cookies=cookies)
        print req.url
    except requests.exceptions.RequestException:
        print "Request Exception."
        #sendEmail("request exception, maybe blocked, maybe maintenance. check it:\n"+url0)
    time.sleep(5)

# Not avaiable for now
#modules.sendEmail("New place available:("+req.url+")"+" check:\n"+url1)

if req.url==url3:
    modules.sendEmail("New place available: "+url1)
    data = {'nextButton':'Etape+suivante'}
    data = urllib.urlencode(data)
    req = requests.post(url=url3,data=data,headers=headers,cookies=cookies)
    print req.url

while req.url==url4 or req.url==url6:
    # If the plage d'horaire not available, it might go back to url4
    if req.url==url4:
        data = {'nextButton':'Premi\xc3re plage horaire libre'}
        data = urllib.urlencode(data)
        req = requests.post(url=url4,data=data,headers=headers,cookies=cookies)
        print req.url

    if req.url==url6:
        url_captcha = "http://www.essonne.gouv.fr/ezjscore/call/bookingserver::captcha"
        req = requests.post(url_captcha, headers=headers, cookies=cookies)

        beg_mp3 = req.content.find("mp3=")+4
        end_mp3 = req.content.find("mp3",beg_mp3+1)+3
        url_mp3 = req.content[beg_mp3:end_mp3]

        beg_jpg = req.content.find("src=")+5 
        end_jpg = req.content.find("jpg")+3
        url_jpg = req.content[beg_jpg:end_jpg]

        local_mp3 = path.join(path.realpath("captcha"), "captcha.mp3")
        local_jpg = path.join(path.realpath("captcha"), "captcha.jpg")
    
        req = urllib2.Request(url_mp3, headers=headers)
        mp3file = urllib2.urlopen(req)
        with open(local_mp3,'wb') as output:
            output.write(mp3file.read())

        req = urllib2.Request(url_jpg, headers=headers)
        jpgfile = urllib2.urlopen(req)
        with open(local_jpg,'wb') as output:
            output.write(jpgfile.read())
    
        local_wav = modules.mp3ToWav(local_mp3)
    
        nCuts = modules.splitWav(local_wav)

        code = ""
        for i in xrange(nCuts):
            local_cut = path.join(path.dirname(path.realpath(local_wav)), "cut_"+str(i)+".wav")
            cut = modules.recognize(local_cut)
            code += cut

        print("Google Speech Recognition thinks the captcha is " + '"' + code + '"')
    
        data = {'eZHumanCAPTCHACode':code.encode('utf-8'),
                'nextButton':'Etape+suivante'}
        data = urllib.urlencode(data)
        req = requests.post(url=url6,data=data,headers=headers,cookies=cookies)
        if req.url==url6:
            # means auto recognition fails
            # saves the files so I can improve the performance
            captchaDir = path.realpath("captcha")
            newDir = path.realpath(modules.makeTimeStampDir(path.join(captchaDir)))
            for file in listdir(captchaDir):
                if file.endswith(".wav") or file.endswith(".mp3") or file.endswith(".jpg"):
                    rename(path.join(captchaDir, file), path.join(newDir, file))
            with open(path.join(newDir, "falseCode.txt"), "w") as text_file:
                text_file.write("%s" % code)
        print req.url

if req.url==url8:
    print "Bravo, you made it to the second last step!!!"
    data = {'firstname':'Gustavo',
            'lastname':'Fring',
            'email':'your-own-email-address',
            'emailcheck':'your-own-email-address',
            'number_agdref':'9910023103',
            'end_date_validity':'09/12/2015',
            'post_code':'91191',
            'nextButton':'Etape+suivante'}
    data = urllib.urlencode(data)
    req = requests.post(url=url8,data=data,headers=headers,cookies=cookies)
    print req.url

if req.url==url9:
    print "You've made it!"
    time.sleep(10)
    url_confirm = modules.confirmRdv()
    if(url_confirm==""):
        print "For some reason, we were not able to confirm the rdv."
    else:
        req = requests.post(url=url_confirm,headers=headers,cookies=cookies)
        print req.url
