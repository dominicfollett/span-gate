#!/usr/bin/env python

from gtts import gTTS
import os

# Everyone
tts = gTTS(text='Good morning', lang='en')
tts.save("good.mp3")

# Willem
tts = gTTS(text='Good morning Villem', lang='en')
tts.save("willem1.mp3")

# Adam
tts = gTTS(text='Guten Morgen, Herr Wayland', lang='de')
tts.save("adam1.mp3")

# Shayan
tts = gTTS(text='Morning Shayan!', lang='en')
tts.save("shayan1.mp3")

# Chris M
tts = gTTS(text='Καλημέρα κ. Μακρυγιαννάκη', lang='el')
tts.save("chris1.mp3")

# Paco
tts = gTTS(text='Bom dia Paco', lang='pt')
tts.save("paco1.mp3")

# Andreas
tts = gTTS(text='Buenas dias Andreas', lang='es')
tts.save("andreas1.mp3")

# Tayla
tts = gTTS(text='Hello Tayla', lang='en')
tts.save("tayla1.mp3")

# Travis
tts = gTTS(text='おはようトラビス', lang='ja')
tts.save("travis1.mp3")