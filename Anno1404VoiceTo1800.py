
try:
  # Skript to convert Anno1404 voicelines to wav.
  # And after you created your soundbank with these wav files, the script creates the assets.xml and text_.xml files for you

  # Das Skript supported nur sehr simple soundbanks, welche bei denen die json pro language nur eine soundbank drin hat
   # und jedes event nur eine IncludedMemoryFiles hat

  # scroll to the bottom to see the ini variables

    
  ######################################################################################
  ######################################################################################
  ######################################################################################

  import subprocess
  import pathlib
  from datetime import datetime
  import traceback
  import time
  import json
  import shutil
  from chardet import detect as chardet_detect # get file encoding type # pip install chardet

  ######################################################################################



  g_Mood = "Neutral"
  g_SpeechAudioType = "Murmur"

  # Anno1800 can only use these four audio languages (tried different, but it uses english)
  # Anno uses english automatically (references languages set in wwise) for all unsupported languages
  Languages_Anno = {"German","English","French","Russian"}
  Languages_bnkToAnno = {"de_de":"German","en_us":"English","fr_fr":"French","ru_ru":"Russian"}


  xml_base = """<ModOps>  
    <!-- uses GUIDs {StartingGUID} to including {EndGUID} -->

    <!-- Positioning: -->
    <!-- for things like shots and stuff that is played without your user interaction at a location ingame, you might want to adjust MaxAttenuation in Audio property -->
    <!-- I think adding a value for MaxAttenuation does not hurt if you dont need any positioning, so I will add it to all Audios. -->
    <!-- Depending on where you use the Sound, the object where you use it must support positioning I think. Eg the Sounds in SoundEmitter of an object -->
    <!--  usually are based on position, while the SoundEmitterCommandBarks voicelines are not. See vanilla for typical postitioned MaxAttenuation values -->

    {SoundBankCode}
    {AssetCode}
    
  </ModOps>"""

  xml_Asset_base = """<ModOp Type="addNextSibling" GUID="224035">
      {AudioAssets}
    </ModOp>"""

  xml_AudioAsset = """    <Asset>
        <Template>Audio</Template>
        <Values>
          <Standard>
            <GUID>{AudioGUID}</GUID>
            <Name>{Eventname}</Name>
          </Standard>
          <Audio>
            <DurationLanguageArray>
              <German>
                <DurationMinimum>{German_DurationMin}</DurationMinimum>
                <DurationMaximum>{German_DurationMax}</DurationMaximum>
              </German>
              <English>
                <DurationMinimum>{English_DurationMin}</DurationMinimum>
                <DurationMaximum>{English_DurationMax}</DurationMaximum>
              </English>
              <French>
                <DurationMinimum>{French_DurationMin}</DurationMinimum>
                <DurationMaximum>{French_DurationMax}</DurationMaximum>
              </French>
              <Russian>
                <DurationMinimum>{Russian_DurationMin}</DurationMinimum>
                <DurationMaximum>{Russian_DurationMax}</DurationMaximum>
              </Russian>
            </DurationLanguageArray>
            <MaxAttenuation>1000000</MaxAttenuation>
          </Audio>
          <WwiseStandard>
            <WwiseID>{EventId}</WwiseID>
          </WwiseStandard>
        </Values>
      </Asset>"""

  xml_AudioTextAsset = """    <Asset>
        <Template>AudioText</Template>
        <Values>
          <Standard>
            <GUID>{AudioTextGUID}</GUID>
            <Name>AudioText {Eventname}: {Text}</Name>
          </Standard>
          <Text />
          <AudioText>
            <AudioAsset>{AudioGUID}</AudioAsset>
            <SpeechAudioType>{SpeechAudioType}</SpeechAudioType>
            <Mood>{Mood}</Mood>
          </AudioText>
        </Values>
      </Asset>"""




  xml_SoundBank_base = """<ModOp Type="addNextSibling" GUID="234859">
      {SoundBankAsset}
    </ModOp>
    <!-- the global sound 9899002 loads before mods, so we have to add our sounds instead to the regions -->
    <ModOp Type="add" GUID="5000001,5000000,160001,114327" Path="/Values/RequiredSoundBanks/SoundBanks">
      {SoundBankEntry}
    </ModOp>
    <!-- if asia region exists (your mod needs to load after that mod) -->
    <ModOp Type="add" GUID="133700001" Path="/Values/RequiredSoundBanks/SoundBanks"
      Condition="@133700001">
      {SoundBankEntry}
    </ModOp>"""
    
  xml_SoundBankAsset = """    <Asset>
        <Template>SoundBank</Template>
        <Values>
          <Standard>
            <GUID>{SoundBankGUID}</GUID>
            <Name>BNK_VO_{SoundBankName}</Name>
            <IconFilename>test_data/graphics/wwise_icons/soundbank.png</IconFilename>
          </Standard>
          <SoundBank>
            <SoundBankLocalized>1</SoundBankLocalized>
          </SoundBank>
          <WwiseStandard>
            <WwiseID>{SoundBankID}</WwiseID>
          </WwiseStandard>
        </Values>
      </Asset>"""
      
  xml_SoundBankEntry = """    <Item>
        <Bank>{SoundBankGUID}</Bank>
      </Item>"""
      
  xml_text_base = """<ModOps>

    <ModOp Type="add" Path="/TextExport/Texts">
      {TextEntries}
    </ModOp>

  </ModOps>"""

  xml_textentry = """    <Text>
        <GUID>{AudioTextGUID}</GUID>
        <Text>{Text}</Text>
      </Text>"""
      



  ######################################################################################


  # convert mp3 to wav file
  def convertmp3towav(inputpath,outputpath): # path with extension .mp3 and .wav
    subprocess.call(['ffmpeg/ffmpeg', '-i', f"{inputpath}", f"{outputpath}"])  # ffmpeg muss in in Umgebungsvariablen als Path gespeichert sein, ist sonst in D:\CDesktopLink\Portable\ffmpeg

  def get_encoding_type(filename):
      try:
          with open(filename, 'rb') as f:
              rawdata = f.read()
          return chardet_detect(rawdata)['encoding']
      except FileNotFoundError as err:
          return None

  def into_path(filename):
      return pathlib.Path(filename) # string umwandeln in path objekt

  def file_exists(filename): # returns True wenn diese Datei/dieser Pfad existiert
      return pathlib.Path(filename).is_file()
      
  def folder_exists(foldername): # returns True wenn dieser Ordner existiert
      return pathlib.Path(filename).is_dir()
  def create_Folder(foldername):
      pathlib.Path(foldername).mkdir(parents=True, exist_ok=True) # create folder       
                
  def GetParentFolderNames(pathobj):
      parentnames = []
      for par in pathobj.parents:
        parentnames.append(par.name)
      return parentnames
                
  def delete_pathfilefolder(pathname): # löscht die Datei oder Ordner an diesem Pfad. Ordner muss leer sein
      path = pathlib.Path(pathname)
      if path.is_file():
          path.unlink(missing_ok=True) # mit missing_ok=False gäbe es ein FileNotFoundError wenns die Datei nicht gibt
      elif path.is_dir():
          try:
            path.rmdir()
          except:
            shutil.rmtree(str(path)) # also deletes filled folders
               
  def rename_file(filename,newfilename,replace=True):# ACHTUNG replace=False, also "rename" funktioniert nur auf Windows. Auf Linux wird immer replaced
      # filename mit Dateiendung übergeben!
      if file_exists(filename):
          if replace:
              pathlib.Path(filename).replace(newfilename) # durch replace: wenn es newfilename bereits gibt, wird sie dadurch überschrieben
          else:
              pathlib.Path(filename).rename(newfilename) # gibt FileExistsError auf Windows wenn es newfilename bereits gibt. Auf Linux wirds aber dennoch replaced!
      else:
          print(f"rename_file: {filename} existiert nicht, kann daher auch nicht umbenannt werden")

  def replaceinvalidchars(Text): # invalid chars for xml
    return Text.replace("<","&lt;").replace(">","&gt;").replace("&","&amp;").replace("\'","&apos;").replace("\"","&quot;")
  
  # \data\loca\eng\txt
  def GetTextFromGUIDsAnno1404(Anno1404_path,GUIDs):
    Anno1404_pathobj = into_path(Anno1404_path)
    Texts = {}
    for AnnoLanguage in Languages_Anno:
      if AnnoLanguage not in Texts:
        Texts[AnnoLanguage] = {}
      lang_foldername = AnnoLanguage=="German" and "ger" or AnnoLanguage=="English" and "eng" or AnnoLanguage=="French" and "fra" or AnnoLanguage=="Russian" and "rus" or None
      if lang_foldername:
        Anno1404_txtpath = f"{Anno1404_pathobj}/data/loca/{lang_foldername}/txt"
        Anno1404_txtpathobj = into_path(Anno1404_txtpath)
        if Anno1404_txtpathobj.is_dir():
          for sub_p in Anno1404_txtpathobj.rglob("*"):
            if sub_p.is_file():
              filename = sub_p.name
              name,ext = filename.split(".")
              if ext=="txt":
                with open(f'{sub_p}', 'r', encoding=get_encoding_type(sub_p)) as f: # most anno1404 txt files have special encoding, without mentioning it here, we can not search the files
                  filetext = f.read()
                  zeilen = list(filetext.split("\n"))
                  for GUID in GUIDs:
                    GUID = str(GUID)
                    if GUID not in Texts[AnnoLanguage] and GUID in filetext:
                      for zeile in zeilen:
                        if GUID in zeile:
                          zeilensplit = zeile.split("=") # 40000009=Agent of the Doge
                          if len(zeilensplit)==2 and GUID==zeilensplit[0]:
                            Text = zeilensplit[1]
                            Text = replaceinvalidchars(Text) # these signs are not allowed in xml text
                            Texts[AnnoLanguage][GUID] = Text
                            break
    return Texts


  def fetchandconvertmp3files(pathobj,Anno1404GUIDs,langsavedestination):
    wavfiles = {}
    lang = langsavedestination.name
    for sub_p in pathobj.rglob("*"): # loop over all sub folders
      if sub_p.is_file():
        filename = sub_p.name
        name,ext = filename.split(".")
        if ext=="mp3":
          try:
            GUID = int(name)
          except ValueError as err: # some 1404 files are named like this: northburgh\200821_b.mp3 or also funny.mp3. ignore them. the "_b" are variations of the same GUID text.
            GUID = None
          if GUID is not None and GUID in Anno1404GUIDs:
            subparname = sub_p.parents[0].name
            wavfilepathob = into_path(f"{langsavedestination}/{subparname}_{GUID}.wav")
            if not wavfilepathob.is_file(): # wav file does not exist yet, then convert it
              convertmp3towav(sub_p,wavfilepathob)
            wavfiles[GUID] = wavfilepathob
    return wavfiles
    
    
  ######################################################################################

  def main():
    
      
    
    wavfiles = {}
    savedestination = f"{YourModFolderObj}/generated"
    create_Folder(savedestination)
    for AnnoLanguage in Languages_Anno:
      wavfiles[AnnoLanguage] = {}
      lang_foldername = AnnoLanguage=="German" and "ger" or AnnoLanguage=="English" and "eng" or AnnoLanguage=="French" and "fra" or AnnoLanguage=="Russian" and "rus" or None
      if lang_foldername:
        langsavedestination = into_path(f"{savedestination}/{lang_foldername}")
        create_Folder(langsavedestination)
        Anno1404_dataspeechobj = into_path(f"{Unpacked1404FilesObj}/data/loca/{lang_foldername}/speech")
        Anno1404_addondataspeechobj = into_path(f"{Unpacked1404FilesObj}/addondata/loca/{lang_foldername}/speech")
        if Anno1404_dataspeechobj.is_dir():
          wavfiles[AnnoLanguage] = fetchandconvertmp3files(Anno1404_dataspeechobj,Anno1404GUIDs,langsavedestination)
        else:
          print("did not find data speech folders")
        if Anno1404_addondataspeechobj.is_dir():
          wavfiles[AnnoLanguage] = fetchandconvertmp3files(Anno1404_addondataspeechobj,Anno1404GUIDs,langsavedestination)
        else:
          print("did not find addondata speech folders")
    
    input(f"\n#########################################\nDone creating the wav files at {savedestination}\nNow use these wav files to create the soundbank(s) with Wwise.\nSee the -HowToUse.txt- file in the Anno1800_wwise folder.\n\nYou can delete the wav files afterwards if you dont need them anymore.\nHitEnter when you are done")
    input(f"\nHit Enter when you put the created soundbank and json files into your Mod folder in data/sound/generatedsoundbanks/windows/...\nThen the script will create the xml files for your mod in the folder {savedestination}\n")
    
    putin = input("\nDo you only want (A)udio or also Audio(T)ext assets and translation text files (for speech/voice you usually need AudioText. for general sounds you do not)\n")
    while putin.upper()!="A" and putin.upper()!="T":
      putin = input("\nDo you only want (A)udio or also Audio(T)ext assets (for speech/voice you usually need AudioText. for general sounds you do not)\n")
    putin = putin.upper()
    
    audioinfos = {}
    soundbankfolderpathobj = into_path(f"{YourModFolderObj}/data/sound/generatedsoundbanks/windows")
    if soundbankfolderpathobj.is_dir():
      SoundBanks = {} # we have at least one bank per language, but maybe even more
      GUIDs = set()
      for sub_p in soundbankfolderpathobj.rglob("*"): # loop over all sub folders
        if sub_p.is_file():
          filename = sub_p.name
          name,ext = filename.split(".")
          if ext=="json":
            with sub_p.open('r', encoding='utf-8') as file:
              data = json.load(file)
              Languagebnk = data["SoundBanksInfo"]["SoundBanks"][0]["Language"] # eg. "de_de"
              SoundBankName = data["SoundBanksInfo"]["SoundBanks"][0]["ShortName"]
              SoundBankID = data["SoundBanksInfo"]["SoundBanks"][0]["Id"]
              AnnoLanguage = Languages_bnkToAnno[Languagebnk]
              if SoundBankID not in SoundBanks:
                SoundBanks[SoundBankID] = {}
              if AnnoLanguage not in SoundBanks[SoundBankID]:
                SoundBanks[SoundBankID][AnnoLanguage] = {"jsonPath":str(sub_p),"SoundBankName":SoundBankName}
              for event in data["SoundBanksInfo"]["SoundBanks"][0]["IncludedEvents"]:
                EventId = event["Id"]
                DurationMin = round(float(event["DurationMin"])*1000)
                DurationMax = round(float(event["DurationMax"])*1000)
                eventname = event["Name"] # "Play_spy_40700606"
                FileID = event["IncludedMemoryFiles"][0]["Id"]
                wavfilename = event["IncludedMemoryFiles"][0]["ShortName"] # "spy_40700606.wav"
                wavname,wavext = wavfilename.split(".")
                filenamesplit = wavname.split("_")
                GUID = filenamesplit[-1]
                try:
                  GUID = int(GUID)
                except ValueError as err:
                  GUID = None
                  print(f"was not able to get GUID out of filename, skipping it: {wavfilename}")
                else:
                  GUIDs.add(GUID)
                if not EventId in audioinfos:
                  audioinfos[EventId] = {}
                audioinfos[EventId][AnnoLanguage] = {"1404GUID":GUID,"FileID":FileID,"DurationMin":DurationMin,"DurationMax":DurationMax,"AnnoLanguage":AnnoLanguage,"Languagebnk":Languagebnk,"SoundBankName":SoundBankName,"SoundBankID":SoundBankID,"Eventname":eventname,"wavfilename":wavfilename}
      
      if putin=="T":
        Texts = GetTextFromGUIDsAnno1404(Unpacked1404Files,GUIDs)
      # audioinfos[EventId][AnnoLanguage] = {"Id":Id,"DurationMin":DurationMin,"DurationMax":DurationMax,"AnnoLanguage":AnnoLanguage,"Languagebnk":Languagebnk,"SoundBankName":SoundBankName,"SoundBankID":SoundBankID,"Eventname":eventname}
      CurrentGUID = StartingGUID
      final_asset_code = ""
      final_text_code = {"Russian":"","German":"","English":"","French":""}
      soundbankentries = ""
      soundbankassets = ""
      soundbanksdone = set() # we have one per language, but the ID is the same and we only need one xml entry
      for SoundBankID,sbinfos in SoundBanks.items():
        for AnnoLanguage,sbinfo in sbinfos.items():
          if SoundBankID not in soundbanksdone:
            SoundBankGUID = CurrentGUID
            SoundBankName = sbinfo["SoundBankName"]
            sbentry = xml_SoundBankEntry.format(SoundBankGUID=SoundBankGUID)
            soundbankentries = f"{soundbankentries}\n{sbentry}"
            sbasset = xml_SoundBankAsset.format(SoundBankID=SoundBankID,SoundBankName=SoundBankName,SoundBankGUID=SoundBankGUID)
            soundbankassets = f"{soundbankassets}\n{sbasset}"
            CurrentGUID += 1
            soundbanksdone.add(SoundBankID)
      final_soundbank_code = xml_SoundBank_base.format(SoundBankAsset=soundbankassets , SoundBankEntry=soundbankentries)
      for EventId,infos in audioinfos.items():
        AudioGUID = CurrentGUID
        CurrentGUID += 1
        if putin=="T":
          AudioTextGUID = CurrentGUID
          CurrentGUID += 1
        Durations = {}
        audio_code = xml_AudioAsset
        filesdone = set() # each file only needs on entry in assets.xml regardless of how many languages
        for AnnoLanguage,info in infos.items():
          Durations[f"{AnnoLanguage}_DurationMax"] = info["DurationMax"]
          try:
            Durations[f"{AnnoLanguage}_DurationMin"] = info["DurationMin"]
          except Exception as err:
            print(infos)
            raise err
          
          if AnnoLanguage=="German":
            audio_code = audio_code.replace("{German_DurationMax}",str(Durations["German_DurationMax"]))
            audio_code = audio_code.replace("{German_DurationMin}",str(Durations["German_DurationMin"]))
          elif AnnoLanguage=="English":
            audio_code = audio_code.replace("{English_DurationMax}",str(Durations["English_DurationMax"]))
            audio_code = audio_code.replace("{English_DurationMin}",str(Durations["English_DurationMin"]))
          elif AnnoLanguage=="French":
            audio_code = audio_code.replace("{French_DurationMax}",str(Durations["French_DurationMax"]))
            audio_code = audio_code.replace("{French_DurationMin}",str(Durations["French_DurationMin"]))
          elif AnnoLanguage=="Russian":
            audio_code = audio_code.replace("{Russian_DurationMax}",str(Durations["Russian_DurationMax"]))
            audio_code = audio_code.replace("{Russian_DurationMin}",str(Durations["Russian_DurationMin"]))
          
          if EventId not in filesdone:
            filesdone.add(EventId)
            Eventname = info["Eventname"]
            audio_code = audio_code.replace("{AudioGUID}",str(AudioGUID)).replace("{SoundBankID}",str(info["SoundBankID"])).replace("{Eventname}",str(Eventname)).replace("{EventId}",str(EventId))
            audiotext_code = ""
          GUID1404 = str(info["1404GUID"])
          if putin=="T":
            Text = Texts[AnnoLanguage].get(GUID1404,"UNKNOWN")
            if Text=="UNKNOWN":
              print(f"Did not find Text for GUID {GUID1404} in Language {AnnoLanguage}")
          
          if AnnoLanguage=="English": # add AudioText when we do english, to add the enlgish text
            GUID1404 = int(GUID1404)
            Mood = GUID1404 in MoodNegativeGUIDs and "Negative" or GUID1404 in MoodPositiveGUIDs and "Positive" or g_Mood
            SpeechAudioType = GUID1404 in SpeechAudioTypeCampaignGUIDs and "Campaign" or GUID1404 in SpeechAudioTypeMovieGUIDs and "Movie" or GUID1404 in SpeechAudioTypePaMSyGUIDs and "PaMSy" or g_SpeechAudioType
            if putin=="T":
              audiotext_code = xml_AudioTextAsset.format(AudioTextGUID=AudioTextGUID,Eventname=Eventname,AudioGUID=AudioGUID,SpeechAudioType=SpeechAudioType,Mood=Mood,Text=Text)
          if putin=="T":
            final_text_code[AnnoLanguage] = f"{final_text_code[AnnoLanguage]}\n{xml_textentry.format(AudioTextGUID=AudioTextGUID,Text=Text)}\n"
          
        final_asset_code = f"{final_asset_code}\n{audio_code}\n{audiotext_code}"
        
      main_code = xml_base.format(StartingGUID=StartingGUID,EndGUID=CurrentGUID,SoundBankCode=final_soundbank_code,AssetCode=xml_Asset_base.format(AudioAssets=final_asset_code))
      if putin=="T":
        for AnnoLanguage,finaltext in final_text_code.items():
          Textxml = xml_text_base.format(TextEntries=finaltext)
          with open(f"{savedestination}/text_{AnnoLanguage.lower()}.xml", "w", encoding='utf-8') as f:
            f.write(Textxml)
      with open(f"{savedestination}/audioassets.include.xml", "w", encoding='utf-8') as f:
        f.write(main_code)
      # print(audioinfos)
      print(CurrentGUID)
      
      
    
    else:
      print(f"did not find the generatedsoundbanks in {soundbankfolderpathobj}")
    
      
      
          


          

  if __name__ == '__main__':
    
    
    # The script needs "ffmpeg/ffmpeg.exe" next to it for the mp3 to wav conversion.
    if not into_path("ffmpeg/ffmpeg.exe").is_file():
      input("This script needs ffmpeg/ffmpeg.exe next to it for the mp3 to wav conversion. Please download it and put it next to this script.\n(if you already have wav files/a finished soundbank, then at least make sure that the wav files you used contain the 1404 GUID, so this script can find them in the 1404 texts)\n")
      exit()

    print("\nYou can abort this script at anytime by hitting Ctrl+C on your keyboard")

    # a list of 1404 GUIDs you want to add as sound
    # assuming that the files in 1404 are all named like GUID.mp3
    # GUIDs entered here should be integers, like 40700606,40700607
    Anno1404GUIDs = input("\nEnter a comma seperated list of Anno1404 GUIDs you want to exctract, eg: 40700606,40700607\nThe mp3 files from 1404 have their GUID as filename.\n").split(",")
    if len(Anno1404GUIDs)==1 and Anno1404GUIDs[0]=="":
      Anno1404GUIDs = []
      input("Seems your list is empty...you can still continue if you already have a finished bnk and json file in your modfolder\n")

    # The mod folder will be used as destination for all new files in a subfolder "generated" which is automatically created
    YourModFolder = input("Enter your mod folder, where your modinfo.json is. (the generated files will be put in there in a newly created -generated- folder)\n") # r"C:\Users\Serpens66\Documents\Anno 1800\mods\Sabotage\shared_SoundsSpy1404"
    YourModFolderObj = into_path(YourModFolder)
    if not YourModFolderObj.is_dir():
      input("Seems this is not a valid folder..abort")
      exit()
    Unpacked1404Files = input("\nEnter your folder which contains the unpacked Anno1404 files (you see data and addondata folders in that folder you add here)\n") # r"D:\CDesktopLink\Unterlagen\Mods\Anno 1800\Anno1800 RDA unpacked\Anno 1404 speech and icons"
    Unpacked1404FilesObj = into_path(Unpacked1404Files)
    if not Unpacked1404FilesObj.is_dir():
      input("Seems this is not a valid folder..abort")
      exit()
    StartingGUID = int(input("\nEnter the starting GUID which will be used in assets.xml of your Anno1800 mod\n")) # for your 1800 mod

    # SpeechAudioType is in vanilla Campaign for Narrator and Murmur for texts your ships are saying. And PaMSy for things the other characters are saying.
    # Mood should bei "Neutral" in most cases, unless it is a audio that is ment to be aggressive (Negative) or very positive (Positve), so mostly relevant for PaMSy of other characters.
    # if Mood/SpeechAudioType should be different than Neutral/Murmur then add the GUIDs here:
    print("\nBy default all AudioText will use -Murmur- and -Neutral- as SpeechAudioType and Mood. If you want different, add the 1404 GUIDs in the next step. Enter nothing for them if you are fine with the default values for all GUIDs.")
    MoodNegativeGUIDs = input("Enter Mood=Negative GUIDs list\n")
    MoodPositiveGUIDs = input("Enter Mood=Positive GUIDs list\n")
    SpeechAudioTypeCampaignGUIDs = input("Enter SpeechAudioType=Campaign GUIDs list\n")
    SpeechAudioTypePaMSyGUIDs = input("Enter SpeechAudioType=PaMSy GUIDs list\n")
    SpeechAudioTypeMovieGUIDs = input("Enter SpeechAudioType=Movie GUIDs list\n")
    
    ###########################################################################
    ######################################################################################

    
    if MoodNegativeGUIDs!="" and "," in MoodNegativeGUIDs:
      MoodNegativeGUIDs = MoodNegativeGUIDs.split(",")
    else:
      MoodNegativeGUIDs = []
    if MoodPositiveGUIDs!="" and "," in MoodPositiveGUIDs:
      MoodPositiveGUIDs = MoodPositiveGUIDs.split(",")
    else:
      MoodPositiveGUIDs = []
    if SpeechAudioTypeCampaignGUIDs!="" and "," in SpeechAudioTypeCampaignGUIDs:
      SpeechAudioTypeCampaignGUIDs = SpeechAudioTypeCampaignGUIDs.split(",")
    else:
      SpeechAudioTypeCampaignGUIDs = []
    if SpeechAudioTypePaMSyGUIDs!="" and "," in SpeechAudioTypePaMSyGUIDs:
      SpeechAudioTypePaMSyGUIDs = SpeechAudioTypePaMSyGUIDs.split(",")
    else:
      SpeechAudioTypePaMSyGUIDs = []
    if SpeechAudioTypeMovieGUIDs!="" and "," in SpeechAudioTypeMovieGUIDs:
      SpeechAudioTypeMovieGUIDs = SpeechAudioTypeMovieGUIDs.split(",")
    else:
      SpeechAudioTypeMovieGUIDs = []
      
    for i,GUID in enumerate(Anno1404GUIDs):
      Anno1404GUIDs[i] = int(GUID) # make all integers
    for i,GUID in enumerate(MoodNegativeGUIDs):
      MoodNegativeGUIDs[i] = int(GUID) # make all integers
    for i,GUID in enumerate(MoodPositiveGUIDs):
      MoodPositiveGUIDs[i] = int(GUID) # make all integers
    for i,GUID in enumerate(SpeechAudioTypeCampaignGUIDs):
      SpeechAudioTypeCampaignGUIDs[i] = int(GUID) # make all integers
    for i,GUID in enumerate(SpeechAudioTypePaMSyGUIDs):
      SpeechAudioTypePaMSyGUIDs[i] = int(GUID) # make all integers
    for i,GUID in enumerate(SpeechAudioTypeMovieGUIDs):
      SpeechAudioTypeMovieGUIDs[i] = int(GUID) # make all integers
      
    
    
    main()
    
    
except Exception as err:
  input(f"ERROR: {err}\n{traceback.format_exc()}")
  raise err
  

      