# -*- coding: utf-8 -*-
#from snips_nlu import SnipsNLUEngine
#from helpers.intent import IntentParser
#from hotword import HotwordDetector
from . import Conversation
from . import CommandHandler
from threading import Thread
import json
import io
from contextlib import redirect_stdout
import subprocess
import collections
import requests
import asyncio
import argparse


HOTWORD = "porcupine"
"""
def get_last_sentences(process):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
"""   
def get_intent(dataset,text):
    """Get intent from transcribed text"""
    
    #return snips.parse(text)
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",type=bool, help="Should wave files be recorded",default=None)
    return parser.parse_args()
def main():
    "Fake Main for debian Script"
    pass
#--------------------------------------------------------------------------------------------------------
"""
hotword=subprocess.Popen(HotwordDetector(
                            library_path=LIBRARY_PATH,
                            model_file_path=MODEL_FILE_PATH,
                            keyword_file_paths=HOTWORD,
                            sensitivities=0.5,
                            output_path=None,
                            input_device_index=None).run(),shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

"""
_ARGS = parse_args()
c=Conversation(aggressiveness=1,savewav=_ARGS.save)
asyncio.run(c.run())
lastsent = collections.deque(maxlen=3)
chandler = CommandHandler()
#intentPars = IntentParser()
"""
while True:
hotwordlog=hotword.stdout.readline()
if(hotwordlog):
print(hotwordlog.strip())
wakeup=True
"""

        
