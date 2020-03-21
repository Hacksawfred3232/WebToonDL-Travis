#!/usr/bin/env python3
import requests_html
import requests
import shlex
import argparse
import os
import glob
from os import mkdir
from sys import exit
from shutil import rmtree as rmdir
from shutil import copytree as cpdir
from shutil import copyfile
import subprocess
import io
from time import sleep
#og:description in property contains the description
#og:title in property contains the name.
#com-linewebtoon:webtoon:author in property contains the author
#split('https')[-1].split('http')[-1].split('://')[-1].split('/')
#Running the code above takes away the http protocol tag and splits the path up.
#The website's Error Tolerance seems to allow us to replace
#the important tags like the genre. This is a form of
#infomation disclosure. Not an exploit/bug, but a interesting
#little quirk and shortcut that can help us do wildcard
#discovery.
#The LI elements on the page contain data-episode-no.
#Their children also contains other infomation under subj, data, and tx.
#If deseprate, running links will grab a link from the LI object.
#Under the same vien, some linux style link redirection is present in the page!

ScriptPath = os.path.dirname(os.path.realpath(__file__))
List_Wildcard_URL = "https://www.webtoons.com/en/GENRE/BOOK/list"
HTML_PI="?"
HTML_PC="&"
Title_Param="title_no="
Page_Param="page="
Episode_Param="episode_no="
DefaultOutput="./<ReplaceNameHere>"

InputArgs = argparse.ArgumentParser(description="Download comics from WEBTOONS!")
InputArgs.add_argument("idtoget", metavar='Comic_ID', type=int, help="ID of the comic to download!")
InputArgs.add_argument("-t, --type", dest="Type", help="Export the comics to given file type (Do -LR to export a list of file types avaliable)", default="JPEG")
InputArgs.add_argument("-Ei, --Episode_id", dest="Epi_ID", help="If you know the ID of a episode, give it here. (Do -EL to export a list of episodes avaliable)", default="0000")
InputArgs.add_argument("-o, --overwrite", dest="Overwrite", help="Overwrite files in the cache.", action="store_true", default=False)
InputArgs.add_argument("-Lt, --List_types", dest="List_Types", help="List file types and exit", action="store_true", default=False)
InputArgs.add_argument("-El --Download_list", dest="Download_list", help="Only display the comic infomation and download a episode list. Don't download any images.", action="store_true", default=False)
InputArgs.add_argument("-O, --output", dest="Output", help="Specify where to output the files. (Default: ./<NAME>)", default=DefaultOutput)
#Static Dictonary containing some cookies to bypass ageGating page
StaticCookies = requests_html.requests.cookies.RequestsCookieJar()
StaticCookies.set('ageGatePass', 'true', domain='.webtoons.com', path='/')
StaticCookies.set('needGDPR', 'true', domain='.webtoons.com', path='/')

def GetPage(URL, Referer=None, Silent=False, DontExit=False):
    Requester= requests_html.HTMLSession()
    #Requester started! Getting Comic listing now!
    if Referer == None:
        if Silent == False:
            print("Trying %s" % URL)
        while True:
            try:
                HTTPHan = Requester.get(URL, cookies=StaticCookies)
                break
            except requests.exceptions.ConnectionError:
                print("ConnectionError occured! Assuming a rate limiter was used. Trying again in 10 seconds.")
                sleep(10)
    else:
        if Silent == False:
            print("Trying %s with Referer %s" % (URL, Referer))
        HEADER = {"Referer":Referer}
        while True:
            try:
                HTTPHan = Requester.get(URL, headers=HEADER)
                break
            except requests.exceptions.ConnectionError:
                print("ConnectionError occured! Assuming a rate limiter was used. Trying again in 10 seconds.")
                sleep(10)
    if (103 < HTTPHan.status_code < 303) == True: # 302 is "Not Modified."
        #Ok! We got a code that is within acceptable paramaters
        #Print a message to inform the user that we have got this far!
        if Silent == False:
            print("Got response! URL is: %s" % HTTPHan.url)
    else:
        #We got something else than the normal code.
        #Check to see if we should display a special message.
        if HTTPHan.status_code == 451:
            #Blast those dang nabit authotarians!
            print("We can not access requested URL for legal reasons. TOR node located in a allowed region required to bypass!")
            Term_Flag=True
        if HTTPHan.status_code in [500,204,205,206,207,208,218,509,526,530,520,521,522,523,524,525,526,527,530,226,502,503,504,505,506,507,508]:
        # Seems we got an server error code!
        # Call the engineers! xD
            print("Trust me, I'm an engineer\nI think we'll put this thing right here\nTrust me, I'm an engineer\nWhat the fuck did just happen here?\nTrust me, I'm an engineer\nWith epic skill and epic gear!\nTrust me, I'm an engineer\nOh shit, I think I'm outta here!")
            print("(We got a server error. Wut!?)")
            Term_Flag=True
        if HTTPHan.status_code in [203,421,511]:
            #We got a proxy return code!
            if Silent == False:
                print("Non-authoritive content detected! Most likely a proxy. We can not confirm that we have a realialbe connection!")
                print("(If you are on a Public Wi-Fi Network, check your captive portal status! If you're sure that you are authorizied, it is no longer safe to stay on this network as this is a possiable sign of a MITM attack! Disconnect ASAP!)")
                print("We will try to run in this state anyway")
                print("Got response! URL is: %s" % HTTPHan.url)
            Term_Flag=False
        if HTTPHan.status_code == 418:
            print("I'M A TEATPOT! I'M A TEATPOT! I'M A TEATPOT! I'M A TEATPOT! I'M A TEATPOT! I'M A TEATPOT!")
            Term_Flag=True
        if Term_Flag == True:
            print("Can not continue execution due to unknown code. Status_code: %d" % HTTPHan.status_code)
            Buffer = HTTPHan.content
            with open("./Buffer.html", "wb") as FileHan:
                FileHan.write(Buffer)
                FileHan.close()
            print("HTML dumped to Buffer.html")
            exit(1)
        else:
            print("Error getting webpage. Status_code: %d" % HTTPHan.status_code)
            return None
    return HTTPHan

ImageFileTypes = ['PNG','JPEG']
BookFileTypes = ['PDF']
ArgsFromCMD = InputArgs.parse_args().__dict__
if ArgsFromCMD['List_Types']:
    for x in ImageFileTypes:
        print("Image: " + x)
    for x in BookFileTypes:
        print("Book: " + x)
    for x in ArchiveTypes:
        print("Archive: " + x)
    exit(0)
if ArgsFromCMD['Type'] not in ImageFileTypes:
    if ArgsFromCMD['Type'] not in BookFileTypes:
        if ArgsFromCMD['Type'] not in ArchiveTypes:
            print("Error! File Type not in Types.")
            exit(0)

HHan = GetPage(List_Wildcard_URL + HTML_PI + Title_Param + str(ArgsFromCMD['idtoget']))
print("Getting comic infomation now.")
#First, get the genre. Its is the most eaist to do.
Comic_Genre= HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[2].capitalize()
#Next, grab the meta infomation.
Metalist= HHan.html.find("meta")
Comic_Name = None
Comic_Author = None
Comic_Description = None
for x in Metalist:
    for y in x.element.attrib:
        if x.element.attrib[y] == "og:title":
            Comic_Name = x.element.attrib['content']
        elif x.element.attrib[y] == "og:description":
            Comic_Description = x.element.attrib['content']
        elif x.element.attrib[y] == "com-linewebtoon:webtoon:author":
            Comic_Author = x.element.attrib['content']

print("Done!")
print("Comic Name: %s" % Comic_Name)
print("Comic Author: %s" % Comic_Author)
print("Comic Genre: %s" % Comic_Genre)
print("Comic Description:\n%s" % Comic_Description)
print("Now indexing...")
#Time out! Before we go any further, i need to explain something about this next bit of code.
#I considered using brute force techniques to try and gather how many pages there will be in a series.
#However, this website does have a throttler algorithim. This was demostrated in the orignal NodeJS version.
#So, a much easier method will be to vist the highest number webpage, and then count again from there.
#A variable flag control will be used here.
#Also, fortuantly for us, a little div element with the paginate class will help us here.
Divlist = HHan.html.find("div")
PagiHTML = None
Comic_EpisodeListing_Pages = [] # Format: {'Page':<PageID>, URL:<URL>}
LP = 0
Last_LP = 0
Last_URL = None
URL = HHan.url
Finished_Flag = False
for x in Divlist:
    try:
        if x.element.attrib['class'] == "paginate":
            PagiHTML = requests_html.HTML(html=x.html)
            break
    except KeyError:
        pass
SortedLinks = list(PagiHTML.links)
#We can safely assume that the first page we are on does exist.
Temporary_Name = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')
del Temporary_Name[0]
Temporary_Name.append(HTML_PC + Page_Param + "1")
Temporary_Name= "/".join(Temporary_Name)
Lang = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[1]
Genre = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[2]
Name = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[3]
Root_URL = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[0]
New_Viewer_URL= "/".join(["https:/",Root_URL,Lang,Genre,Name,"list"])
Comic_EpisodeListing_Pages.append({'Page':1, 'URL':Temporary_Name})
while Finished_Flag != True:
    for x in SortedLinks:
        PageNo= int(x[-1])
        if {'Page':PageNo, 'URL':x} in Comic_EpisodeListing_Pages:
            pass
        else:
            LP = PageNo
    if LP == Last_LP:
        Finished_Flag = True
    else:
        Last_LP = LP
        Last_URL = URL
        TemporaryHan = GetPage(New_Viewer_URL + HTML_PI + Title_Param + str(ArgsFromCMD['idtoget']) + HTML_PC + Page_Param + str(LP), Referer=URL)
        DivlistTemp = TemporaryHan.html.find("div")
        URL = TemporaryHan.url
        for x in Divlist:
            try:
                if x.element.attrib['class'] == "paginate":
                    PagiHTML = requests_html.HTML(html=x.html)
                    break
            except KeyError:
                pass
counter = 1
FailCounter = 0
Episodes = [] # Format {Episode_id:<ID>, Count:<Count>, URL:<URL> Name:<NAME>, Date:<Date>}
LastKnownList = None
for c in range(1,10000000):
    if FailCounter == 3:
      print("Ran into 3 dead pages, we assume that we ran out of pages to check. Breaking loop...")
      break
    print("Getting listings from page %d" % c)
    TemporaryHan = GetPage(New_Viewer_URL + HTML_PI + Title_Param + str(ArgsFromCMD['idtoget']) + HTML_PC + Page_Param + str(c), Referer=URL, Silent=True, DontExit=True)
    if TemporaryHan == None:
      print("Page %d does not exist. Skipping..." % c)
      FailCounter = FailCounter + 1
      continue
    Last_URL = URL
    URL = TemporaryHan.url
    LiList = TemporaryHan.html.find("li")
    if str(LiList) == LastKnownList:
      print("We ran into a duplicatle listing. Assumed we hit the end. Breaking loop...")
      break
    LastKnownList = str(LiList)
    for x in LiList:
        for y in x.element.attrib:
            if y == "data-episode-no":
                Name = None
                Date = None
                SpanList = x.find("span")
                for z in SpanList:
                    try:
                        if z.attrs['class'][0] == "subj":
                            Name = z.text
                            Name = Name.split("BGM")[0]
                        elif z.attrs['class'][0] == "date":
                            Date = z.text
                    except KeyError:
                        pass
                if len(str(x.element.attrib['data-episode-no'])) == 1:
                    Str_Data_Episode_No = "000" + str(x.element.attrib['data-episode-no'])
                elif len(str(x.element.attrib['data-episode-no'])) == 2:
                    Str_Data_Episode_No = "00" + str(x.element.attrib['data-episode-no'])
                elif len(str(x.element.attrib['data-episode-no'])) == 3:
                    Str_Data_Episode_No = "0" + str(x.element.attrib['data-episode-no'])
                else:
                    Str_Data_Episode_No = str(x.element.attrib['data-episode-no'])
                Episodes.append({'Episode_id':Str_Data_Episode_No, 'Count':counter, 'URL':list(x.links)[0], 'Name':Name, 'Date':Date})
                counter = counter + 1
SortedEpisodes = []
counter = 1
while True:
    for x in Episodes:
        if x['Count'] == counter:
            SortedEpisodes.append(x)
            counter = counter + 1
    if len(SortedEpisodes) == len(Episodes):
        break
    else:
        continue
SortedEpisodes = SortedEpisodes[::-1]
if ArgsFromCMD['Download_list'] == True:
    print("Exporting the list of episodes!")
    with open(("./%s-Episodes.txt" % HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[3]), "w") as EpisodeTXT:
        for x in SortedEpisodes:
            EpiID = x['Episode_id']
            Name = x['Name']
            Date = x['Date']
            Date = Date.split()
            Date[1] = Date[1].split(",")[0]
            Date = "_".join(Date)
            EpisodeTXT.write("#ID:%s %s %s at url %s\n" % (EpiID, Name, Date, x['URL']))
    print("Done!")
    exit(0)
#Oh boy. Now here comes the fun bit.
#What we have to do is to index and sort the images in the correct order.
#The _images class contains our comic images. Our other tool version managed to sort the images? I don't know. We will see tho.
#It also appears that we need to refer the correct episode when downloading images. So let's set up our variables.
Root_URL = "www.webtoons.com"
Comic_RawName = HHan.url.split('https')[-1].split('http')[-1].split('://')[-1].split('/')[3]
if ArgsFromCMD['Output'] == DefaultOutput:
    OutputDirectory = "".join([DefaultOutput.split("<ReplaceNameHere>")[0], Comic_RawName])
    try:
        mkdir(OutputDirectory)
    except:
        pass
else:
    OutputDirectory = "".join([ArgsFromCMD['Output'], "/", Comic_RawName])
    try:
        mkdir(ArgsFromCMD['Output'])
    except:
        pass
    try:
        mkdir(OutputDirectory)
    except:
        pass
if ArgsFromCMD['Type'] == 'JPEG':
    print("JPEG selected (or no other type selected).")
    print("We will just copy the tmp folder to output.")
    OutputType = "JPEG"
else:
    if ArgsFromCMD['Type'] in ImageFileTypes:
        print("%s selected. This is a Image File Type." % ArgsFromCMD['Type'])
        print("Import Image to handle conversion.")
        try:
            from PIL import Image
            print("OK!")
            print("Setting Output Type from Args.")
            OutputType = ArgsFromCMD['Type']
        except ImportError:
            print("Failure!")
            print("Falling back to JPEG exporting.")
            OutputType = "JPEG"
    elif ArgsFromCMD['Type'] in BookFileTypes:
        print("%s selected. This is a Book file type." % ArgsFromCMD['Type'])
        print("Looking for Tool for this type.")
        if ArgsFromCMD['Type'] == "PDF":
            print("Importing fpdf")
            try:
                import fpdf
                print("OK!")
                print("Importing Image to handle Image conversion.")
                from PIL import Image
                print("OK!")
                print("Setting Output Type.")
                OutputType = "PDF"
            except ImportError:
                print("Failure!")
                print("Falling back to JPEG exporting.")
                OutputType = "JPEG"

if len(str(ArgsFromCMD['Epi_ID'])) < 4:
    print("Are you sure you typed in the ID correctly? Try padding the number out.")
    print("E.G 1 becomes 0001")
for x in SortedEpisodes:
    if ArgsFromCMD['Epi_ID'] != "0000":
        if ArgsFromCMD['Epi_ID'] != x['Episode_id']:
            continue
    DirectoryName = "_".join(x['Name'].split())
    try:
        mkdir(ScriptPath + "/cache/")
    except FileExistsError:
        pass
    try:
        mkdir(ScriptPath + "/cache/" + Comic_RawName)
    except FileExistsError:
        pass
    try:
        mkdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName)
        mkdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp")
        print("Downloading %s" % x['Name'])
        ContinueFlag = True
    except FileExistsError:
        if ArgsFromCMD['Overwrite'] == True:
            print("Overwriting %s" % x['Name'])
            rmdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName)
            mkdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName)
            mkdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp")
            ContinueFlag = True
        else:
            print("%s already exists!" % x['Name'])
            print("Just performing conversion.")
            ContinueFlag = False
    if ContinueFlag == True:
        Episode_URL = x['URL']
        Episode_Content = GetPage(Episode_URL, Referer=Root_URL, Silent=True)
        ImageList = Episode_Content.html.element[0].find_class("_images")
        counter = 1
        Images = [] # Format: {Name:<Name>, Data:<Data>}
        for y in ImageList:
            ImageURL = y.attrib['data-url']
            ImageHan = GetPage(ImageURL, Referer=Episode_URL, Silent=True)
            if len(str(counter)) == 1:
                str_counter = "000" + str(counter)
            elif len(str(counter)) == 2:
                str_counter = "00" + str(counter)
            elif len(str(counter)) == 3:
                str_counter = "0" + str(counter)
            else:
                str_counter = str(counter)
            ImageName = ("Page_%s.jpg" % str_counter)
            Images.append({"Name":ImageName, 'Data':ImageHan.content})
            counter = counter + 1
        for z in Images:
            with open(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp/" + z['Name'], "wb") as ImageFile :
                ImageFile.write(z['Data'])
                ImageFile.close()
#Phew! Now we have all episodes downloaded, lets go ahead and proceed with conversion.
    if OutputType == 'JPEG':
        cpdir(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp", OutputDirectory + "/" + DirectoryName + "/output")
    elif OutputType in ImageFileTypes:
        mkdir(OutputDirectory + "/" + DirectoryName)
        for z in glob.glob(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp/*.jpg"):
            ImaHan = Image.open(z)
            FileName = z.split("/")[-1].split(".")[0] + "." + OutputType.lower()
            ImaHan.save(OutputDirectory + "/" + DirectoryName + "/" + FileName)
    elif OutputType == 'PDF':
        PDF_file = fpdf.FPDF(unit="pt", format="a4")
        ImageFilesList = glob.glob(ScriptPath + "/cache/" + Comic_RawName + "/" + DirectoryName + "/tmp/*.jpg")
        ImageFilesList.sort()
        for z in ImageFilesList:
            ImageTemp = Image.open(z)
            ImgWidth, ImgHeight = (ImageTemp.size[0] / 96 * 72, ImageTemp.size[1] / 96 * 72)
            ImageTemp.close()
            if ImgWidth > ImgHeight:
                PDF_file.add_page(orientation="L")
                try:
                    PDF_file.image(z,0,0,841.89,595.28)
                except:
                    print("Image Error detected! %s" % z)
                    print("Attempting auto repair!")
                    try:
                        ImageTemp = Image.open(z)
                        ImageTemp = ImageTemp.convert("RGB")
                        ImageTemp.save(z)
                        PDF_file.image(z,0,0,841.89,595.28)
                        print("Repair complete!")
                    except Exception as e:
                        print("Repiar failure! Image skipped!")
                        print("Error is: %s" % e)
            else:
                PDF_file.add_page(orientation="P")
                try:
                    PDF_file.image(z,0,0,595.28,841.89)
                except:
                    print("Image Error detected! %s" % z)
                    print("Attempting auto repair!")
                    try:
                        ImageTemp = Image.open(z)
                        ImageTemp = ImageTemp.convert("RGB")
                        ImageTemp.save(z)
                        PDF_file.image(z,0,0,595.28,841.89)
                        print("Repair complete!")
                    except Exception as e:
                        print("Repiar failure! Image skipped!")
                        print("Error is: %s" % e)
        PDF_file.output(OutputDirectory + "/" + DirectoryName + ".pdf", "F")
    print("Done!")
