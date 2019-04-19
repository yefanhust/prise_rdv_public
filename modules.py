# -*- coding: latin-1 -*-

import os, errno
import time 
import datetime 

def makeTimeStampDir(dir):
    '''
    Mimic mkdir -p using the time stamp as the path name. 
    '''
    ts = time.time()
    path = os.path.join(dir, datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S'))
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
    return path

def makeDir(dir):
    '''
    Mimic mkdir -p using a given name
    '''
    if not os.path.exists(os.path.realpath(dir)):
        try:
            os.makedirs(os.path.realpath(dir))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return os.path.realpath(dir)


from os import path
def scheduler():
    '''
    Pick next client. Smaller number, higher priority.
    '''
    queued = path.realpath("queued")
    list = [x for x in os.listdir(queued) if not x.startswith('.')]
    list.sort()
    if(len(list)==0):
        return ""
    return path.join(queued,list[0])

def readInfo(path):
    '''
    Read client's submission data. 
    '''
    with open(path, "r") as f:
        l=f.readlines()
        pInfo = {'firstname':l[0].split("=")[1][:-1],
                 'lastname':l[1].split("=")[1][:-1],
                 'email':l[2].split("=")[1][:-1],
                 'emailcheck':l[3].split("=")[1][:-1],
                 'number_agdref':l[4].split("=")[1][:-1],
                 'end_date_validity':l[5].split("=")[1][:-1],
                 'post_code':l[6].split("=")[1][:-1],
                 'nextButton':'Etape+suivante',
                 'lastTol':l[7].split("=")[1][:-1]}
        #edate = pInfo["end_date_validity"].split('/')
        #end_date = datetime.date(int(edate[2]), int(edate[1]), int(edate[0]))
        #today = datetime.date.today()
        #if end_date<today:
        #    return 0
        if len(pInfo["post_code"])!=5:
            return 1
        if len(pInfo["number_agdref"])!=10:
            return 2
        return pInfo

###### Email processing ######

import smtplib 
# Allow less secure apps from google in order for SMTP to work
# (Now service.saclay, songluzheng2 and zuji.france have allowed this.)
# Disable the gmail alert: Gear icon -> Gmail settings -> General -> Enable Gmail Notifications
# Check the following when sendEmail fails because of SMTPAuthenticationError
# http://stackoverflow.com/questions/26697565/django-smtpauthenticationerror

def sendEmail(msg, msg_subj, sender, password, receiver):
    '''
    Send a email by any sender in gmail to any receiver using password. 
    For univ-lille1 mail: smtpServer="smtps.univ-lille1.fr:587"
    '''
    smtpServerList = {"gmail.com":"smtps.gmail.com:587",
                      "hotmail.com":"smtp-mail.outlook.com:587",
                      "outlook.com":"smtp-mail.outlook.com:587",
    }
    smtpServer = smtpServerList[sender.split("@")[1]]
    try:
        cc = []
        bcc = []
        message = "From: %s\r\n" % sender \
                  + "To: %s\r\n" % receiver \
                  + "CC: %s\r\n" % ",".join(cc) \
                  + "Subject: %s\r\n" % msg_subj \
                  + "\r\n" + msg
        # Credentials (if needed)
        username = sender
        # The actual mail send
        receiver = [receiver] + cc + bcc
        smtpObj = smtplib.SMTP(smtpServer)
        smtpObj.starttls()
        smtpObj.login(username, password)
        smtpObj.sendmail(sender, receiver, message)
        print "Successfully sent email"
        smtpObj.quit()
    except smtplib.SMTPAuthenticationError:
        print "Authentication failed."
    except smtplib.SMTPException:
        print "Error: unable to send email."


import imaplib
import email 
def confirmRdv(username, password):
    '''
    Confirm the Rdv by clicking the link in a gmail that have just been sent.
    '''
    imapServerList = {"gmail.com":"imap.gmail.com",
                      "hotmail.com":"imap-mail.outlook.com",
    }
    dns = username.split("@")[1]
    imapServer = imapServerList[dns]
    
    mail = imaplib.IMAP4_SSL(imapServer)
    mail.login(username, password)
    mail.select("inbox") # connect to inbox.
    result, data = mail.uid('search', None, "ALL") # search and return uids instead
    for uid in reversed(data[0].split()):
        print "Now processing uid:",uid
        result, data = mail.uid('fetch', uid, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_string(raw_email)
        print email_message
        if email.utils.parseaddr(email_message['From'])[1]=="ide_booking@hebergement2.interieur-gouv.fr" and email.utils.parseaddr(email_message['Subject'])[1]=="Demande":
            print "Right mail found."
            if dns=="gmail.com":
                url_beg = raw_email.find("Vous disposez de 5 minutes pour confirmer ou supprimer votre demande de rendez-vous.")
                url_beg = raw_email.find("http", url_beg)
                url_end = raw_email.find('"',url_beg)
                return raw_email[url_beg:url_end]
            if dns=="hotmail.com":
                url_beg = raw_email.find("http")
                url_end = raw_email.find('"',url_beg)
                x=raw_email[url_beg:url_end]
                #y=x.split("=")
                #print y
                return raw_email[url_beg:url_end].replace("=\r\n","")
    return ""

###### Audio processing ######

import wave
import struct
from random import randint
def splitWav(filename):
    '''
    Extract all individual words and save them into separate wav files.
    '''
    #ip = wave.open(sys.argv[1], 'r')
    ip = wave.open(filename, 'r')
    info = ip.getparams()
    frame_list = []
    for i in range(ip.getnframes()):
        sframe = ip.readframes(1)
        amplitude = struct.unpack('<h', sframe)[0]
        frame_list.append(amplitude)
    ip.close()
    for i in range(0,len(frame_list)):
        if abs(frame_list[i]) < 25:
            frame_list[i] = 0
    ###### Find Out most louder portions of the audio file ######
    thresh = 30
    output = []
    nonzerotemp = []
    length = len(frame_list)
    i = 0
    while i < length:
        zeros = []
        while i < length and frame_list[i] == 0:
            i += 1
            zeros.append(0)
        if len(zeros) != 0 and len(zeros) < thresh:
            nonzerotemp += zeros
        elif len(zeros) > thresh:
            if len(nonzerotemp) > 0 and i < length:
                output.append(nonzerotemp)
                nonzerotemp = []
        else:
            nonzerotemp.append(frame_list[i])
            i += 1
    if len(nonzerotemp) > 0:
        output.append(nonzerotemp)
 
    chunks = []
    for j in range(0,len(output)):
        if len(output[j]) > 3000:
            chunks.append(output[j])
    
    ###########################################################

    for l in chunks:
        for m in range(0,len(l)):
            if l[m] == 0:
                l[m] = randint(-0,+0)
 
    inc_percent = 1 #10 percent
 
    for l in chunks:
        for m in range(0,len(l)):
            if l[m] <= 0:
                # negative value
                l[m] = 0 - abs(l[m]) + abs(l[m])*inc_percent/100
            else:
                #positive vaule
                l[m] =     abs(l[m]) + abs(l[m])*inc_percent/100

    ###########################################################
 
    # Below code generates separate wav files depending on the number of loud voice detected.
 
    NEW_RATE = 1 #Change it to > 1 if any amplification is required
 
    print '[+] Possibly ',len(chunks),'number of loud voice detected...'
    for i in range(0, len(chunks)):
        new_frame_rate = info[0]*NEW_RATE
        print '[+] Creating No.',str(i),' file..'
        output_path = path.join(path.dirname(path.realpath(filename)), "cut_"+str(i)+".wav")
        split = wave.open(output_path, 'w')
        split.setparams((info[0],info[1],info[2],0,info[4],info[5]))
        #split.setparams((info[0],info[1],new_frame_rate,0,info[4],info[5]))
 
        #Add some silence at start selecting +15 to -15
        for k in range(0,10000):
            single_frame = struct.pack('<h', randint(-25,+25))
            split.writeframes(single_frame)
        # Add the voice for the first time
        for frames in chunks[i]:
            single_frame = struct.pack('<h', frames)
            split.writeframes(single_frame)
        #Add some silence in between two digits
        #for k in range(0,10000):
        #    single_frame = struct.pack('<h', randint(-25,+25))
        #    split.writeframes(single_frame)
        # Repeat effect :  Add the voice second time
        #for frames in chunks[i]:
        #    single_frame = struct.pack('<h', frames)
        #    split.writeframes(single_frame)
        #Add silence at end
        #for k in range(0,10000):
        #    single_frame = struct.pack('<h', randint(-25,+25))
        #    split.writeframes(single_frame)
        split.close()#Close each files

    return len(chunks)

from pydub import AudioSegment
def mp3ToWav(mp3):
    '''
    Transform a mp3 file into a wav file.
    '''
    song = AudioSegment.from_mp3(mp3)
    mp3_name = path.basename(mp3)
    wav = path.join(path.dirname(path.realpath(mp3)), mp3_name.split(".")[0]+".wav")
    song.export(wav, format = "wav")
    return wav

import speech_recognition as sr
correction = {u"à":"A",
              "art":"A",
              "Arte":"A",
              "un":"A",
              u"bébé":"B",
              "b***":"B",
              "beeg":"B",
              "billet":"B",
              "des":"B",
              "c'est":"C", 
              "euh":"E",
              "j'ai":"G",
              u"âge":"H",
              "Gigi":"J",
              "Gilly":"J",
              "gîte":"J",
              "il y":"J",
              "Julie":"J",
              "car":"K",
              "caca":"K",
              "carte":"K",
              "quand":"K",
              "ta":"K",
              "elle":"N",
              "et":"P",
              "pmu":"P",
              "PSG":"P",
              "TV":"P",
              "c**":"Q",
              u"créer":"Q",
              "qui":"Q",
              "tu":"Q",
              "air":"R",
              "est-ce":"S",
              "tee":"T",
              "tu es":"T",
              "Hugo":"U",
              "YouTube":"U",
              "the":"V",
              "zizi":"V",
              "if":"X",
              "hit":"X",
              "CAF":"4",
              "cat":"4",
              "15":"4",
              "saint":"5",
              "psy":"6",
              "Hugues":"8",
              "neuf":"9", 
              "ne":"9",
              "non":"9",
}
def recognize(wav):
    '''
    Recognize a wav file in French. 
    '''
    r = sr.Recognizer()
    with sr.WavFile(wav) as source:
        audio = r.record(source)
    # recognize speech using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        ret = r.recognize_google(audio, language="fr_FR")
    except sr.UnknownValueError:
        ret = ""
    except sr.RequestError:
        ret = ""
    if ret in correction:
        ret = correction[ret]
    return ret.upper()

###### RDV Manager ######

import shutil
import urllib
import urllib2
import requests

def endDateIn_pInfo(pInfo):
     edate = pInfo["end_date_validity"].split('/')
     return datetime.date(int(edate[2]), int(edate[1]), int(edate[0]))

def firstDateOfNextYear():
    thisyear = datetime.datetime.now().strftime("%Y")
    return datetime.date(int(thisyear)+1, 1, 1)

class RdvManager:
    '''
    Help you better manage your rendez-vous. First all, grab one!
    '''
    def __init__(self, headers, cookies, urlBase="http://www.essonne.gouv.fr/booking/create/14056/"):
        self.headers=headers
        self.cookies=cookies
        self.url=[urlBase]*10
        for i in xrange(10):
            self.url[i]+=str(i)

    def violateLastToleratedDateForUrl6(self, req, pInfo):
        if(req.url!=self.url[6]):
            return False
        beg = req.content.find("<label>Date</label>")
        beg = req.content.find("<span>",beg)
        end = req.content.find("</span>",beg)
        date = req.content[beg+6:end]
        date = date.split()
        monthlist={"janvier":1,u"février":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,u"août":8,"septembre":9,"octobre":10,"novembre":11,u"décembre":12}
        weekday,day,month,year = date[0],int(date[1]),monthlist[date[2].decode("utf-8")],int(date[3])
        #print weekday,day,month,year
        today = datetime.date.today()
        lastTol = pInfo["lastTol"].split('/')
        try:
            lastTol = datetime.date(int(lastTol[2]),int(lastTol[1]),int(lastTol[0]))
        except ValueError:
            lastTol = datetime.date.max
        rdvDate = datetime.date(year, month, day)
        
        if rdvDate>lastTol or rdvDate<today:
            print "rdv date "+weekday,rdvDate,"has violated last tolerated date",lastTol 
            print "(%s)" % (datetime.datetime.now().strftime("%Y-%m-%d,%H:%M:%S"))
            return True
        return False

    def grabRdv(self, pInfo, rdvMailAddr):
        '''
        Grab a rendez-vous using provided personal information.
        '''
        print "The client's info:"
        print pInfo
        # url1 
        data = {
            'planning':'15992',
            'nextButton':'Etape+suivante'}
        data = urllib.urlencode(data)
        req = requests.post(url=self.url[1], data=data, headers=self.headers, cookies=self.cookies)
        c = 0
        while req.url!=self.url[3]:
            c += 1
            print "%d (%s)" % (c, datetime.datetime.now().strftime("%Y-%m-%d,%H:%M:%S"))
            try:
                req = requests.post(url=self.url[1], data=data, headers=self.headers, cookies=self.cookies)
                print req.url
            except requests.exceptions.RequestException:
                print "Request Exception."
            time.sleep(3)
        
        # url3
        if req.url==self.url[3]:
            data = {'nextButton':'Etape+suivante'}
            data = urllib.urlencode(data)
            req = requests.post(url=self.url[3],data=data,headers=self.headers,cookies=self.cookies)
            print req.url
            
        # url4 or url6
        while req.url==self.url[4] or req.url==self.url[6]:
            # If the plage d'horaire not available, it might go back to url4
            if req.url==self.url[4]:
                data = {'nextButton':'Premi\xc3re plage horaire libre'}
                data = urllib.urlencode(data)
                req = requests.post(url=self.url[4],data=data,headers=self.headers,cookies=self.cookies)
                print req.url
            while self.violateLastToleratedDateForUrl6(req, pInfo):
                data = {'nextButton':'Premi\xc3re plage horaire libre'}
                data = urllib.urlencode(data)
                req = requests.post(url=self.url[4],data=data,headers=self.headers,cookies=self.cookies)
                print req.url
           
            url_captcha = "http://www.essonne.gouv.fr/ezjscore/call/bookingserver::captcha"
            req = requests.post(url_captcha, headers=self.headers, cookies=self.cookies)

            beg_mp3 = req.content.find("mp3=")+4
            end_mp3 = req.content.find("mp3",beg_mp3+1)+3
            url_mp3 = req.content[beg_mp3:end_mp3]

            beg_jpg = req.content.find("src=")+5 
            end_jpg = req.content.find("jpg")+3
            url_jpg = req.content[beg_jpg:end_jpg]

            local_mp3 = path.join(makeDir("captcha"), "captcha.mp3")
            local_jpg = path.join(makeDir("captcha"), "captcha.jpg")
        
            req = urllib2.Request(url_mp3, headers=self.headers)
            mp3file = urllib2.urlopen(req)
            with open(local_mp3,'wb') as output:
                output.write(mp3file.read())

            req = urllib2.Request(url_jpg, headers=self.headers)
            jpgfile = urllib2.urlopen(req)
            with open(local_jpg,'wb') as output:
                output.write(jpgfile.read())

            local_wav = mp3ToWav(local_mp3)
    
            nCuts = splitWav(local_wav)
            
            code = ""
            for i in xrange(nCuts):
                local_cut = path.join(path.dirname(path.realpath(local_wav)), "cut_"+str(i)+".wav")
                cut = recognize(local_cut)
                code += cut
                
            print("Google Speech Recognition thinks the captcha is " + '"' + code + '"')
            if(len(code)!=5):
                code = recognize(local_wav)
                code = "".join(code.split())
                print("Second shot: "+code)
            data = {'eZHumanCAPTCHACode':code,
            'nextButton':'Etape+suivante'}
            data = urllib.urlencode(data)
            req = requests.post(url=self.url[6],data=data,headers=self.headers,cookies=self.cookies)
            if req.url==self.url[6]:
                # means auto recognition fails
                # saves the files so I can improve the performance
                captchaDir = path.realpath("captcha")
                newDir = path.realpath(makeTimeStampDir(path.join(captchaDir)))
                for file in os.listdir(captchaDir):
                    if file.endswith(".wav") or file.endswith(".mp3") or file.endswith(".jpg"):
                        shutil.copy(path.join(captchaDir, file), path.join(newDir, file))
                with open(path.join(newDir, "falseCode.txt"), "w") as text_file:
                    text_file.write("%s" % code)
            print req.url

        if req.url==self.url[8]:
            print "Bravo, you made it to the second last step!!!"
            pInfo.pop("lastTol",None)
            print pInfo
            data = urllib.urlencode(pInfo)
            req = requests.post(url=self.url[8],data=data,headers=self.headers,cookies=self.cookies)
            print req.url

        while req.url==self.url[8] and endDateIn_pInfo(pInfo)<firstDateOfNextYear():
            end_date = endDateIn_pInfo(pInfo) + datetime.timedelta(days=1)
            pInfo["end_date_validity"] = end_date.strftime("%d/%m/%Y")
            print pInfo
            data = urllib.urlencode(pInfo)
            req = requests.post(url=self.url[8],data=data,headers=self.headers,cookies=self.cookies)
            print req.url
            
        if req.url==self.url[9]:
            print "You've made it!"
            time.sleep(10)
            
            username = pInfo["email"]
            alias={"alias-for-your-email-address":"your-email-address"}
            if username in alias.keys():
                username = alias[username]

            alias_tete = {"email-address-header":"your-email-address"}
            tete = username.split('@')[0].split('_')[0]
            if tete in alias_tete.keys():
                username = alias_tete[tete]

            print username
            password = rdvMailAddr[username]

            url_confirm = confirmRdv(username, password)
            if(url_confirm==""):
                print "For some unknown reason, we were not able to confirm the rdv."
                return 0
            else:
                print "Extracted confirm url: "+url_confirm
                req = requests.post(url=url_confirm,headers=self.headers,cookies=self.cookies)
                print "The response of confirmation: "+req.url
                return req.url

        print req.url
        errorDir = path.realpath("error")
        with open(path.join(errorDir, "url8_"+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+".html"), "w") as html_file:
            html_file.write("%s" % req.content)
        print "There is probably sth wrong with the client's info. For more information please see the directory \"error\"."
        return 0
