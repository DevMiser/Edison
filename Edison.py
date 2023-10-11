import board
import boto3
import datetime
import io
import openai
import os
import pvcobra
import pvleopard
import pvporcupine
import pyaudio
import random
import re
import struct
import subprocess
import sys
import textwrap
import threading
import time
import vlc
#import pytz #uncomment to select timezone

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

from adafruit_ht16k33.segments import Seg7x4
from colorama import Fore, Style
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance
from pvleopard import *
from pvrecorder import PvRecorder
from threading import Thread, Event
from time import sleep

import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
led1_pin=18
GPIO.setup(led1_pin, GPIO.OUT)
GPIO.output(led1_pin, GPIO.LOW)

i2c = board.I2C()
display = Seg7x4(i2c)
display.brightness = 1.0 #can be adjusted between 0.0 and 1.0
display.blink_rate = 0
display.colon = True

audio_stream = None
cobra = None
pa = None
polly = boto3.client('polly')
porcupine = None
recorder = None
wav_file = None

GPT_model = "gpt-4" # most capable GPT model and optimized for chat

openai.api_key = "put your secret API key between these quotation marks"
pv_access_key= "put your secret access key between these quotation marks"

prompt = ["How may I assist you?",
    "How may I help?",
    "What can I do for you?",
    "Ask me anything.",
    "Yes?",
    "I'm here.",
    "I'm listening.",
    "What would you like me to do?"]

chat_log=[
    {"role": "system", "content": "You are a helpful assistant."},
    ]

#Edison will 'remember' earlier queries so that it has greater continuity in its response
#the following will delete that 'memory' three minutes after the start of the conversation
def append_clear_countdown():
    sleep(180)
    global chat_log
    chat_log.clear()
    chat_log=[
        {"role": "system", "content": "You are a helpful assistant."},
        ]    
    global count
    count = 0
    t_count.join

def ChatGPT(query):
    user_query=[
        {"role": "user", "content": query},
        ]
    send_query = (chat_log + user_query)
    response = openai.ChatCompletion.create(
    model=GPT_model,
    messages=send_query
    )
    answer = response.choices[0]['message']['content']
    chat_log.append({"role": "assistant", "content": answer})
    return str.strip(response['choices'][0]['message']['content'])

def change_station(transcript):
    
    global Chat
    global Radio
    
    transcript_l = transcript.lower()
    if any(word in transcript_l for word in ["change", "play", "switch"]) and \
       any(word in transcript_l for word in ["radio", "station", "channel", "music"]):
        print ("A request to change the radio station was detected")
        if "classical" in transcript_l:
            radio_url = "http://tuner.classical102.com:80/"
            print ("Playing classical")
        elif "mandarin" in transcript_l:
            radio_url = "http://s1.voscast.com:10556/stream"
            print ("Playing Mandarin")
        elif "french" in transcript_l:
            radio_url = "http://direct.franceinter.fr/live/franceinter-midfi.mp3"
            print ("Playing French")
        elif "acoustic" in transcript_l:
            radio_url = "http://ec5.yesstreaming.net:1910/stream"
            print ("Playing acoustic music")
        elif "calm" in transcript_l:
            radio_url = "http://streaming503.radionomy.com/calmradio-solo-piano-guitar"
            print ("Playing calm music")
        elif "rock" in transcript_l:
            radio_url = "http://audio-edge-es6pf.mia.g.radiomast.io/c2cc99fb-efdf-485d-bcec-be38ba20e2bb"
            print ("Playing Rock music")
        elif "pop" in transcript_l:
            radio_url = "http://pstnet6.shoutcastnet.com:60210/stream"
            print ("Playing Pop music")
        elif "guitar" in transcript_l:
            radio_url = "http://radio.ericksons.net:8000/cgnw"
            print ("Playing guitar music")
        elif "spa" in transcript_l:
            radio_url = "https://ec3.yesstreaming.net:1950/stream"
            print ("Playing spa music")
        else:
            radio_url = "https://ec3.yesstreaming.net:1950/stream"            
            print ("Playing French")
        print(radio_url)
        media = instance.media_new(radio_url)
        player.set_media(media)
        player.audio_set_volume(70)  #integer between 0-100
        player.play()
        Radio = 1
        Chat = 0
    else:
        pass
            
def clock_request(transcript):
    
    global Chat

    transcript_l = transcript.lower()
    if ("stop" in transcript_l or "off" in transcript_l or "start"\
        in transcript_l or "on" in transcript_l or "dim" in transcript_l\
        or "darken" in transcript_l or "brighten" in transcript_l)\
        and ("clock" in transcript_l or "display" in transcript_l):
        print ("A request to change the clock was detected")
        if "stop" in transcript_l or "off" in transcript_l:
            print ("\nTurning off the clock")
            clock_event.set()
            display.fill(0)
        elif "dim" in transcript_l or "darken" in transcript_l:
            print ("\nDimming the display")
            display.brightness = 0.3
        elif "brighten" in transcript_l:
            print ("\nBrightening the display")
            display.brightness = 1.0        
        if "start" in transcript_l or "on" in transcript_l:            
            print ("\nTurning on the clock")
            clock_thread = threading.Thread(target=display_time, args=(clock_event,))
            clock_thread.start()
        else:
            pass
        voice("Done")
        sleep(0.2)
            
        Chat = 0
        
def current_time():

    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%m-%d-%Y %I:%M %p\n")
    print("The current date and time is:", formatted_time)  

def detect_silence():

    cobra = pvcobra.create(access_key=pv_access_key)

    silence_pa = pyaudio.PyAudio()

    cobra_audio_stream = silence_pa.open(
                    rate=cobra.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=cobra.frame_length)

    last_voice_time = time.time()

    while True:
        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)
           
        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 1.3:
                print("End of query detected\n")
                GPIO.output(led1_pin, GPIO.LOW)
                cobra_audio_stream.stop_stream                
                cobra_audio_stream.close()
                cobra.delete()
                last_voice_time=None
                break

def display_time(clock_event):
    
    clock_event.clear()
    while not clock_event.is_set():
        now = datetime.datetime.now()
#        now = datetime.datetime.now(pytz.timezone('Etc/GMT')) #uncomment to select timezone
        time = now.strftime("%l:%M")
        display.print(time)
        sleep(0.2)
        
def fade_led_filament(event):
    
    pwm1 = GPIO.PWM(led1_pin, 200)

    event.clear()

    while not event.is_set():
        pwm1.start(0)
        for dc in range(0, 101, 5):
            pwm1.ChangeDutyCycle(dc)  
            time.sleep(0.05)
        time.sleep(0.75)
        for dc in range(100, -1, -5):
            pwm1.ChangeDutyCycle(dc)                
            time.sleep(0.05)
        time.sleep(0.75)
        
def listen():

    cobra = pvcobra.create(access_key=pv_access_key)

    listen_pa = pyaudio.PyAudio()

    listen_audio_stream = listen_pa.open(
                rate=cobra.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=cobra.frame_length)

    print("Listening...")

    while True:
        listen_pcm = listen_audio_stream.read(cobra.frame_length)
        listen_pcm = struct.unpack_from("h" * cobra.frame_length, listen_pcm)
           
        if cobra.process(listen_pcm) > 0.3:
            print("Voice detected")
            listen_audio_stream.stop_stream
            listen_audio_stream.close()
            cobra.delete()
            break
        
def responseprinter(chat):
    
    wrapper = textwrap.TextWrapper(width=70)  # Adjust the width to your preference
    paragraphs = res.split('\n')
    wrapped_chat = "\n".join([wrapper.fill(p) for p in paragraphs])
    for word in wrapped_chat:
       time.sleep(0.055)
       print(word, end="", flush=True)
    print()

def radio_request(transcript):
    
    global Chat
    global Radio
    
    transcript_l = transcript.lower()
    
    if any(word in transcript_l for word in ["stop", "off", "start", "on", "mute"]) and \
       any(word in transcript_l for word in ["radio", "music", "sound"]):
        print ("A request to change the radio status was detected")
        if "stop" in transcript_l or "off" in transcript_l or "mute" in transcript_l:
            print ("\nTurning off the radio")
            Radio = 0
            player.stop()
            voice("Done")
        if "start" in transcript_l or "on" in transcript_l or "play" in transcript_l:            
            print ("\nTurning on the radio")
            Radio = 1
            player.play()
            clock_thread = threading.Thread(target=display_time, args=(clock_event,))
            clock_thread.start()
        else:
            pass
        Chat = 0
        sleep(0.5)     

def voice(chat):
   
    voiceResponse = polly.synthesize_speech(Text=chat, OutputFormat="mp3",
                    VoiceId="Matthew") #other options include Amy, Joey, Nicole, Raveena and Russell
#                    VoiceId="Matthew", Engine="neural") #use this line instead of the one above to use the neural engine
    if "AudioStream" in voiceResponse:
        with voiceResponse["AudioStream"] as stream:
            output_file = "speech.mp3"
            try:
                with open(output_file, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                print(error)

    else:
        print("did not work")

    pygame.mixer.init()     
    pygame.mixer.music.load(output_file)
#    pygame.mixer.music.set_volume(0.8) # uncomment to control the the playback volume (from 0.0 to 1.0  
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    sleep(0.2)

def wake_word():
    
    global Radio

   porcupine = pvporcupine.create(keywords=["computer", "jarvis", "Edison",],
                            access_key=pv_access_key,
                            sensitivities=[0.1, 0.1, 0.4], #from 0 to 1.0 - a higher number reduces
                                   #the miss rate at the cost of increased false alarms                              
                                   )
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    
    wake_pa = pyaudio.PyAudio() # pause the vlc player

    porcupine_audio_stream = wake_pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)
    
    Detect = True

    while Detect:
        porcupine_pcm = porcupine_audio_stream.read(porcupine.frame_length)
        porcupine_pcm = struct.unpack_from("h" * porcupine.frame_length, porcupine_pcm)

        porcupine_keyword_index = porcupine.process(porcupine_pcm)

        if porcupine_keyword_index >= 0:

            GPIO.output(led1_pin, GPIO.HIGH)
            if Radio == 1:            
                player.stop()
            else:
                pass
            print(Fore.GREEN + "\nWake word detected\n")
            current_time()
            porcupine_audio_stream.stop_stream
            porcupine_audio_stream.close()
            porcupine.delete()         
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            sleep (0.2)         
            Detect = False

class Recorder(Thread):
    def __init__(self):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm

try:

    o = create(
        access_key=pv_access_key,
        )
    
    event = threading.Event()

    clock_event = threading.Event()
    clock_thread = threading.Thread(target=display_time, args=(clock_event,))
    clock_thread.start()

    instance = vlc.Instance()
    instance.log_unset()
    player = instance.media_player_new()
    media = instance.media_new('http://streaming503.radionomy.com/calmradio-solo-piano-guitar')
    player.set_media(media)
    player.audio_set_volume(70)  #integer between 0-100

    global Radio

    Radio = 0
    
    count = 0

    while True:
        
        try:
            Chat = 1
            if count == 0:
                t_count = threading.Thread(target=append_clear_countdown)
                t_count.start()
            else:
                pass   
            count += 1
            wake_word()
# uncomment the next line if you want Edison to verbally respond to his name        
#            voice(random.choice(prompt))
            recorder = Recorder()
            recorder.start()
            listen()
            detect_silence()
            transcript, words = o.process(recorder.stop())
            t_fade = threading.Thread(target=fade_led_filament, args=(event,))
            t_fade.start()
            recorder.stop()
            print("You said: " + transcript)
            change_station(transcript)
            radio_request(transcript) 
            clock_request(transcript)

            if Chat == 1:        
                (res) = ChatGPT(transcript)
                print("\nEdison's response is:\n")        
                t1 = threading.Thread(target=voice, args=(res,))
                t2 = threading.Thread(target=responseprinter, args=(res,))

                t1.start()
                t2.start()

                t1.join()
                t2.join()

            if Radio == 1:
                player.play()
                print("Radio is on")
            else:
                print("Radio is off")
                pass

            event.set()
            GPIO.output(led1_pin, GPIO.LOW)  
            recorder.stop()
            o.delete
            recorder = None
            
        except openai.error.APIError as e:
            print("\nThere was an API error.  Please try again in a few minutes.")
            voice("\nThere was an A P I error.  Please try again in a few minutes.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.error.Timeout as e:
            print("\nYour request timed out.  Please try again in a few minutes.")
            voice("\nYour request timed out.  Please try again in a few minutes.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.error.RateLimitError as e:
            print("\nYou have hit your assigned rate limit.")
            voice("\nYou have hit your assigned rate limit.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            break

        except openai.error.APIConnectionError as e:
            print("\nI am having trouble connecting to the API.  Please check your network connection and then try again.")
            voice("\nI am having trouble connecting to the A P I.  Please check your network connection and try again.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.error.AuthenticationError as e:
            print("\nYour OpenAI API key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            voice("\nYour Open A I A P I key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            break

        except openai.error.ServiceUnavailableError as e:
            print("\nThere is an issue with OpenAI’s servers.  Please try again later.")
            voice("\nThere is an issue with Open A I’s servers.  Please try again later.")
            event.set()
            GPIO.output(led1_pin, GPIO.LOW)
            GPIO.output(led2_pin, GPIO.LOW)        
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)
          
except KeyboardInterrupt:
    print("\nExiting ChatGPT Virtual Assistant")
    o.delete
    GPIO.cleanup()
