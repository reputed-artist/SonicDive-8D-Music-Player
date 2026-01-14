from pydub import AudioSegment

# Load MP3 file
mp3 = AudioSegment.from_mp3(r"C:\Users\codetech engineers\Desktop\CA DATA\side menu tutorial\side menu tutorial\02 - Tere Liye - MusicBadshah.Com.mp3")

# Export as WAV
mp3.export("song.wav", format="wav")

print("Converted successfully → song.wav")
