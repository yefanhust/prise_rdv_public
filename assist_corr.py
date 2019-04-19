#!/usr/bin/env python

import os
import speech_recognition as sr
import modules

#dir = os.path.realpath(sys.argv[1])
dir = [os.path.realpath("captcha/"+x) for x in os.listdir("captcha") if x.startswith("2")]
for d in dir:
    print d
    r = sr.Recognizer()
    with sr.WavFile(os.path.join(d,"captcha.wav")) as source:
        audio = r.record(source)
    print r.recognize_google(audio,language="fr_FR")
    lcuts = [x for x in os.listdir(d) if x.startswith("cut")]
    jpg = os.path.join(d, [x for x in os.listdir(d) if x.endswith("jpg")][0])
    for i in lcuts:
        cut = os.path.join(d, i)
        with sr.WavFile(cut) as source:
            audio = r.record(source)
        try:
            raw = r.recognize_google(audio, language="fr_FR")
        except sr.UnknownValueError:
            raw = ""
        except sr.RequestError:
            raw = ""
        if len(raw)>1 and not modules.correction.has_key(raw):
            print i+":",
            print raw+"(currently being recognized as: "+modules.recognize(cut)+")"
            #os.system('open '+jpg) 
