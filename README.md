Created by Serpens66 Anno1800 Modder 09.07.2025  
https://github.com/Serpens66/Anno-1800-Mods  

Script used to convert Anno 1404 Voicelines to Anno 1800.  
(normal sounds not supported by the script, but can be adjusted by changing the search path of 1404 files.  
The Wwise Project has SFX Mixxer with 3d sound (positional) enabled, but it is untested and I dont know what values such sounds in 1800 assets.xml need)  
  
The Wwise 1800 project can be used for all your sound additions, it is kind of a pre set up template with several settings already done.  
  
  
This script requires https://ffmpeg.org/download.html#build-windows to convert mp3 to wav.  
I included the file here, because although it is legit, the website really looks super fishy and hard to find the correct download.  

Use the python script (or the exe) to get and convert mp3 files from Anno1404 to wav.  
Then install Wwise with "Wwise Install v2019.2.15_Build7667" (https://www.audiokinetic.com/en/download/) it is free, but you have to register your email. Installation can take roughly 20 minutes.  
Then use the Anno1800_wwise_Project (read the HowToUse.txt) in it, to create the soundbanks with these wav files.  
Then continue to use the python script (or exe) to create the assets.xml/text_.xml file for your 1800 mod.  

To unpack files from Anno 1404/1800 you need the game files and this unpacker:  
https://github.com/lysanntranvouez/RDAExplorer

More information on adding sounds to Anno 1800:  
https://a1800mod.github.io/#/en/tutorials/sounds  
https://github.com/anno-mods/modding-guide/blob/main/guides/Add%20Sounds.md  
