import concurrent.futures
import requests
import asyncio,logging
import os,io
import configparser
from halo import Halo
import deepspeech
import numpy as np
import glob,json
from threading import Thread
from .conversation import VADAudio
import collections
import time
import led

RESTSERVER='http://192.168.178.17:12101/api'
THRESHOLD=1
LOGPATH="/sasha_sentence_logger/sasha_sentence_logger/transcript.txt"
EVALPATH = "/sasha_sentence_logger/sasha_sentence_logger/benchmark_pi4.csv"
TRAIN_PATH="/sasha_sentence_logger/sasha_sentence_logger/benchmark_train.csv"
COMMAND_START=0.0
COMMAND_END=0.0
TRANSCRIPTION_END = 0.0
EXECUTION_START =0.0
TRAIN_START=0.0
TRAiN_END =0.0
SAVE_CMD=0.0
ADAPT_START=0.0
RECORDNO =0
STARTED = False
logging.getLogger("asyncio").setLevel(logging.DEBUG)

class Server():
    """
    Abstract the connection to the API through this Server class.
    """

    def __init__(self):
        self.url=""
        self.data=""
        self.content_type=""

    def set_url(self, url):
        """
        Combine the base API url with the required resource

        Args:
            url (str): The url  of the requested resource without leading slash
        """
        self.url = RESTSERVER + '/' + url

    def set_content_type(self, type):
        """
        Define the 'Content-Type' header.

        Args:
            type (str): The content type, e.g. 'application/json'
        """
        self.content_type = {'Content-Type': type}
        
    def set_data(self, data):
        """
        Set the body data, that should be send to the request.

        Args:
            data (str|collection): Data can be string or object
        """
        self.data = data

    def get(self):
        """
        Send a GET request and return the response.

        Returns:
            requests.Response: The answer provided by the server
        """
        print("GET",self.url)
        return requests.get(self.url,headers=self.content_type,json=self.data)

    def post(self):
        """
        Send a POST request and return the response.

        Returns:
            requests.Response: The answer provided by the server
        """
        print("POST",self.url)
        return requests.post(self.url,headers=self.content_type,json=self.data)
    
    def addCommand(self,command, intent):
        """
        Trigger the API to add a new command and update the intent.

        Args:
            command (str): The name of the command
            intent (str): The intent, the command belongs to

        Returns:
            requests.Response: The answer provided by the server
        """
        data = {intent: [command]}
        
        self.set_url('slots')
        self.set_content_type('application/json')
        self.set_data(data)

        return self.post()
    def getSlots(self):
        """
        Get existing Slots from Rhasspy API

        Returns:
            requests.Response: Json containing existing slots
        """
        self.set_url('slots')
        return self.get()
    def train(self):
        """
        Force the server to train the known commands and intents.

        Returns:
            requests.Response: The answer provided by the server
        """
        self.set_url('train')

        return self.post()

    def tts(self, command, intent):
        """
        Trigger the server to read out the given command and intent.

        Args:
            command (str): The name of the command
            intent (str): The intent, the command belongs to

        Returns:
            requests.Response: The answer provided by the server
        """
        data = 'Now you can use ' + command + ' to trigger ' + intent
        self.set_url('text-to-speech')
        self.set_data(data)
        return self.post()

    def get_intents(self):
        """
        Receive all intents from the API.

        Returns:
            requests.Response: The answer provided by the server
        """
        self.set_url('sentences')
        return self.get()
    
    def save_intents(self,intents):
        """[summary]

        Args:
            intents ([type]): [description]

        Returns:
            [type]: [description]
        """
        self.set_url('sentences')
        self.set_content_type('octet-stream')
        self.set_data(intents)
        return self.post()
    
    def text_to_intent(self,intent,implicit=False):
        """[summary]

        Args:
            intent ([type]): [description]
            implicit (bool, optional): [description]. Defaults to False.

        Returns:
            [type]: [description]
        """
        self.set_url('text-to-intent?implicit='+ str(implicit))
        self.set_data(intent)
        return self.post()


    




class Conversation():
    """Class for transcribing recorded speech or stream from Microphon to Text with deepspeech. It loads a deepspeech tflite model and scorer from 
    /lib/deepspeech, splits the audio stream in sentences with voice activity detection and prints recognised sentences 
    to stdout. If wavfile is set to a path analysis is done on the file instead. Specifying savewav path records the streamed audio to a file """
    def __init__(
            self,
            aggressiveness,
            device=None,
            input_rate=16000,
            wavfile=None,
            savewav=None,
            pauselength=300,
            nospinner=False,
            no_logging = False,
            hotword ="porcupine"):
    
        """
        :param aggresiveness: Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 3
        :param device: Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().
        :param input_rate: Input device sample rate. Your device may require 44100.
        :param wavfile: Read from .wav file instead of microphone
        :param savewav: Save .wav files of utterences to given directory
        :param pauselength: Set length of pauses between sentences. Default  is 300ms.
        :param nospinner: Disable spinner.
        :param no_logging: Disable logging conversation to text file.

        """
        self.aggressiveness=aggressiveness
        self.device=device
        self.input_rate =input_rate
        self.wavfile = wavfile
        self.savewav=savewav
        self.pauselength=pauselength
        self.nospinner=nospinner
        self.hotword=hotword
        self.no_logging=no_logging
        #Initialise DeepSpeech model
        logging.info('Initializing model...')
        dirname = os.getcwd()
        parentdir = os.path.split(dirname)[1]
        logging.info(parentdir)
        model_name = glob.glob(os.path.join(dirname,'lib/*.tflite'))[0]
        scorer_name = glob.glob(os.path.join(dirname,'lib/*.scorer'))[0]
        logging.info("Model: %s", model_name)
        logging.info("Language model: %s", scorer_name)
        self.model = deepspeech.Model(model_name)
        self.model.enableExternalScorer(scorer_name)
        self.started = False
    def save_to_file(self,path:str,line:str):
        """
        Saves the line to a text file

        Args:
            line(str): Line of transcribed text
        """
        if os.path.isfile(path):
            mode = "a"
        else:
            mode = "w"
        backup = open(path, mode)
        backup.write(line+"\n")
        backup.close

    async def run(self):
        """
        Transcribes Conversation line fand send transcription to Command Handler.
        """
        try:
            
            # Start audio with VAD
            vad_audio = VADAudio(
                            self.aggressiveness,
                            self.device,
                            self.input_rate,
                            self.wavfile,
                            )
            cHandler=CommandHandler()
            backlog = collections.deque(maxlen=3)

            logging.info("Listening (ctrl-C to exit)...")
            frames = vad_audio.vad_collector(self.pauselength)

            # Stream from microphone to DeepSpeech using VAD
            spinner = None
            if not self.nospinner:
                spinner = Halo(spinner='line')
            stream_context = self.model.createStream()
            wav_data = bytearray()
            for frame in frames:
                if frame is not None:
                    if spinner and not self.started: 
                        spinner.start()
                        global COMMAND_START
                        COMMAND_START=time.perf_counter()
                        self.started= True
                        logging.info("Command Start")
                    logging.debug("streaming frame")
                    stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                    if self.savewav: 
                        wav_data.extend(frame)
                else:
                    if spinner: 
                        spinner.stop()
                    global COMMAND_END
                    COMMAND_END=time.perf_counter()
                    self.started=False
                    logging.debug("end utterence")
                    line = stream_context.finishStream()
                    if (line):
                        global RECORDNO
                        RECORDNO+=1
                        logging.info(str(RECORDNO)+" Recognized: %s \n Detecting Wakeword..." % line)
                        global TRANSCRIPTION_END
                        TRANSCRIPTION_END = time.perf_counter()
                        #Posting the data to local command handler
                        backlog.append(line)
                        WAV_LEN=str(COMMAND_END-COMMAND_START)
                        STT_LEN=str(TRANSCRIPTION_END-COMMAND_END)
                        logging.info("WAV Length: %s STT-Transcription Time: %s",WAV_LEN,STT_LEN)
                        global EXECUTION_START
                        if self.hotword in line and len(line) != len(self.hotword):
                            Thread(target=led.startWorkingBlink).start()
                            hw_recognised=True
                            line=line.replace(self.hotword,'')
                            intentname = cHandler.recognize_intent(line=line) 
                            EXECUTION_START = time.perf_counter()
                            logging.info("Intent Recognition Time: %s Execution Started after %s",str(EXECUTION_START-TRANSCRIPTION_END),str(EXECUTION_START-COMMAND_END))
                            led.stopWorkingBlink()
                            if intentname:
                                potcommands=[]
                                for potcmd in backlog:
                                    potcommands.append(potcmd)
                                thread= Thread(target=cHandler.adapt_intents,args=(potcommands,intentname))
                                thread.start()
                                #loop.run_in_executor(None,cHandler.adapt_intents(backlog,intentname))
                                
                        elif self.hotword not in line:
                            EXECUTION_START = time.perf_counter()
                            intentname = cHandler.recognize_intent(line=line,implicit=True)
                            hw_recognised=False
                        if(not self.no_logging):
                            self.save_to_file(line=line,path=LOGPATH)
                        if self.savewav:
                            wav_name="command_recording_b("+str(RECORDNO)+").wav"
                            vad_audio.write_wav(os.path.join(self.savewav,wav_name ), wav_data)
                            wav_data = bytearray()
                            benchmarkline = ";".join([wav_name,WAV_LEN,STT_LEN,str(EXECUTION_START-TRANSCRIPTION_END),line,intentname,str(hw_recognised)])  
                            self.save_to_file(line=benchmarkline,path=EVALPATH)
                    stream_context = self.model.createStream()
        except KeyboardInterrupt:
            print('stopping...')
        finally:
            if vad_audio is not None:
                vad_audio.destroy()

class CommandHandler():
    """Class for recognising and modifying commands 
    """
    def __init__(self):
        self.potentials={}
        self.server = Server()

    def recognize_intent(self,line,implicit=False):
        """
        Recognise intent and return the resulting name

        Args:
            line (str): line of transcribed text
            implicit (bool, optional): Was a hot word detected in the command? Defaults to False.

        Returns:
            str: IntentName
        """
        res=self.server.text_to_intent(line,implicit)
        try: 
            return res.json()["intent"]["name"]
        except TypeError:
            return None

    def adapt_intents(self,backlog:list,intentname:str):
        """Adapt intent patterns with sentences that occured before the command. If any commands were added retrain the assistant.

        Args:
            backlog (list): list of last sentences before the recognised intent
            intentname (str): Name of recognised intent
        """
        global ADAPT_START
        ADAPT_START= time.perf_counter()
        update_list:list(tuple)=[]
        for index,potential in enumerate(backlog):
            updated = False
            if index<len(backlog):
                potcmd =  self.save_potential_intent(intentname,potential)
                if potcmd > THRESHOLD:
                    global TRAIN_START
                    TRAIN_START= time.perf_counter()
                    updated=self.update_intents(intentname,potential)
                    logging.info("Update Required:%s",str(updated))
            if updated:
                update_list.append(updated)
        SAVE_CMD = time.perf_counter()
        # Train if new command detected
        if len(update_list)>0:
            self.server.train()
            global TRAIN_END
            TRAIN_END=time.perf_counter()
            logging.info("Training Done After %s s",str(TRAIN_END-TRAIN_START))
            for intent,command in update_list:
                benchmark_line=";".join([intent,command,str(TRAIN_END-TRAIN_START),str(SAVE_CMD-ADAPT_START)])
                self.save_to_file(TRAIN_PATH,benchmark_line)
                self.server.tts(command, intent)

    def save_potential_intent(self,intent:str,potential:str):
        """
        Save the sentences leading up to the command and return the occurence. 
        Args:
            intent(str): name of the intent which was recognized
            potential(str): Transcribed sentence leading up to the command
        
        Returns:
            int: occurence of potential new commands for this intent
        """
        preIntents = {}
        if not intent in self.potentials.keys():
            self.potentials[intent]=preIntents
        preIntents = self.potentials[intent]
        occurence = 0
        if not potential in preIntents.keys():
            preIntents[potential]=occurence
        occurence = preIntents[potential]+1
        preIntents[potential] = occurence
        self.potentials[intent] = preIntents
        print(self.potentials)
        return occurence
    
    def save_to_file(self,path:str,line:str):
        """
        Saves the line to a text file

        Args:
            line(str): Line of transcribed text
            path(str): Path to the file where the line should be stored
        """
        if os.path.isfile(path):
            mode = "a"
        else:
            mode = "w"
        backup = open(path, mode)
        backup.write(line+"\n")
        backup.close   
    
    def addCommand(self,command,intent):
        """Add Command to Slot Values 

        Args:
            command (str): New command that should be recognised
            intent (str): intent that should be connected with the command
        """
        req = self.server.getSlots()
        slots=req.json()
        added = False
        if not command in slots[intent]:
            r = self.server.addCommand(command, intent)
            added = r.text == 'OK'
        return added
        
    
    def update_intents(self,intent:str,newTrigger):
        """Get sentences.ini file from Rhasspy and include slot variable if necessary. Then add the command.
        Args:
            intent (str): Intentname that will be adapted
            newTrigger (str): New trigger that should be recognised
        Returns:
            [type]: [description]
        """
        res = self.server.get_intents()
        slotsVar = "$"+intent.lower()+"{"+intent.lower()+"}"
        cparse= configparser.ConfigParser(allow_no_value=True)
        cparse.read_string(res.text)
        commands=list(cparse[intent].keys())
        logging.info("Command List %s", commands)
        #Checking if slot var already exists
        if not slotsVar in commands:
            print("Not included:",slotsVar)
            cparse.set(intent,slotsVar)
            with io.StringIO() as update:
                cparse.write(update)
                self.server.save_intents(update.getvalue())
        if self.addCommand(newTrigger,intent):
            return (newTrigger,intent)
