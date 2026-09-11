from pydub import AudioSegment
import os

wav_file = '/Users/juhn/Desktop/agent/trans/R20260525-145000.WAV'
m4a_file = '/Users/juhn/Desktop/agent/trans/test.m4a'

sound = AudioSegment.from_file(wav_file, format='WAV')

sound.export(m4a_file, format='mp4', codec = 'aac')
os.remove('/Users/juhn/Desktop/agent/trans/R20260525-145000.WAV')
print('OK')