#!/usr/bin/env python
#ADAPTED FROM 'OBAMENU' VERSION 1.1.7  ! 

#see here and here1

#additional categories

#Building
#Debugger
#IDE
#GUIDesigner
#Profiling
#RevisionControl
#Translation
#Calendar
#ContactManagement
#Database
#Dictionary
#Chart
#Email
#Finance
#FlowChart
#PDA
#ProjectManagement
#Presentation
#Spreadsheet
#WordProcessor
#2DGraphics
#VectorGraphics
#RasterGraphics
#3DGraphics
#Scanning
#OCR
#Photography
#Publishing
#Viewer
#TextTools
#DesktopSettings
#HardwareSettings
#Printing
#PackageManager
#Dialup
#InstantMessaging
#Chat
#IRCClient
#FileTransfer
#HamRadio
#News
#P2P
#RemoteAccess
#Telephony
#TelephonyTools
#VideoConference
#WebBrowser
#WebDevelopment
#Midi
#Mixer
#Sequencer
#Tuner
#TV
#AudioVideoEditing
#Player
#Recorder
#DiscBurning
#ActionGame
#AdventureGame
#ArcadeGame
#BoardGame
#BlocksGame
#CardGame
#KidsGame
#LogicGame
#RolePlaying
#Simulation
#SportsGame
#StrategyGame
#Art
#Construction
#Music
#Languages
#Science
#ArtificialIntelligence
#Astronomy
#Biology
#Chemistry
#ComputerScience
#DataVisualization
#Economy
#Electricity
#Geography
#Geology
#Geoscience
#History
#ImageProcessing
#Literature
#Math
#NumericalAnalysis
#MedicalSoftware
#Physics
#Robotics
#Sports
#ParallelComputing
#Amusement
#Archiving
#Compression
#Electronics
#Emulator
#Engineering
#FileTools
#FileManager
#TerminalEmulator
#Filesystem
#Monitor
#Security
#Accessibility
#Calculator
#Clock
#TextEditor
#Documentation
#Core
#KDE
#GNOME
#GTK
#Qt
#Motif
#Java
#ConsoleOnly

#reserved categories
#Screensaver
#TrayIcon
#Applet
#Shell
################################################################################


import os
import re
import sys
import Globals

#https://standards.freedesktop.org/menu-spec/latest/apas02.html
applications_dirs = ("/usr/share/applications","~/.gnome/apps","~/.kde/share/apps","/usr/share/applications/kde4" )
image_dir_base = "/usr/share" # without "pixmaps" -/usr/local/share in FreeBSD, /usr/share on linux
icon_Theme = "Humanity"
image_cat_prefix = "applications-"  # if empty will create no icon text only menu
application_groups = (
"Office",
"Science",
"Development",
"Graphics",
"Internet",
"Games",
"System",
"Multimedia",
"Utilities",
"DesktopSettings",
"Mixer",
"FileManager",
"Documentation",
"Settings",
"TerminalEmulator",
"Monitor"
)

group_aliases = {"Audio":"Multimedia","AudioVideo":"Multimedia","Network":"Internet","Game":"Games", "Utility":"Utilities", "GTK":"",  "GNOME":""}
ignoreList = ("evince-previewer", "Ted",  "wingide3.2", "python3.4", "feh","xfce4-power-manager-settings" )
terminal_string = "evte -e"         # your favourites terminal exec string
simpleOBheader = False  # print full xml style OB header
# --- End of user config ---
 
import glob
import os.path

class dtItem(object):
    def __init__(self, fName):
        self.fileName = fName
        self.Name = ""
        self.Comment = ""
        self.Exec = ""
        self.Terminal = None
        self.Type = ""
        self.Icon = ""
        self.Categories = ()

    def addName(self, data):
        self.Name = xescape(data)

    def addComment(self, data):
        self.Comment = data

    def addExec(self, data):
        if len(data) > 3 and data[-2] == '%':	# get rid of filemanager arguments in dt files
            data = data[:-2].strip()
        self.Exec = data

    def addIcon(self, data):
        self.Icon = ""
        if image_cat_prefix == "":
            return
        image_dir = image_dir_base + "/pixmaps/"
        di = data.strip()
        if len(di) < 3:
            #"Error in %s: Invalid or no icon '%s'" % (self.fileName,  di)
            return
        dix = di.find("/")      # is it a full path?
        if dix >= 0 and dix <= 2:    # yes, its a path (./path or ../path or /path ...)
            self.Icon = di
            return
        #else a short name like "myapp"
        tmp = image_dir + di + ".*"
        tmp = glob.glob(tmp)
        if len(tmp) > 0:
            self.Icon = tmp[0]
        return

    def addTerminal(self, data):
        if data == "True" or data == "true":
            self.Terminal = True
        else:
            self.Terminal = False

    def addType(self, data):
        self.Type = data

    def addCategories(self, data):
        self.Categories = data

def getCatIcon(cat):
    iconDir = image_dir_base + "/icons/" + icon_Theme + "/categories/24/"
    cat = image_cat_prefix + cat.lower()
    tmp = glob.glob(iconDir + cat + ".*")
    if len(tmp) > 0:
        return tmp[0]
    return ""

def xescape(s):
    Rep = {"&":"&amp;", "<":"&lt;", ">":"&gt;",  "'":"&apos;", "\"":"&quot;"}
    for p in ("&", "<", ">",  "'","\""):
        sl = len(s); last = -1
        while last < sl:
            i = s.find(p,  last+1)
            if i < 0:
                done = True
                break
            last = i
            l = s[:i]
            r = s[i+1:]
            s = l + Rep[p] + r
    return s

def process_category(cat, curCats,  appGroups = application_groups,  aliases = group_aliases ):
	# first process aliases
	if aliases.has_key(cat):
		if aliases[cat] == "":
			return ""                               # ignore this one
		cat = aliases[cat]
	if cat in appGroups and cat not in curCats:  # valid categories only and no doublettes, please
		curCats.append(cat)
		return cat
	return ""


def process_dtfile(dtf,  catDict):  # process this file & extract relevant info
	active = False          # parse only after "[Desktop Entry]" line
	fh = open(dtf,  "r")
	lines = fh.readlines()
	this = dtItem(dtf)
	for l in lines:
		l = l.strip()
		if l == "[Desktop Entry]":
			active = True
			continue
		if active == False:     # we don't care about licenses or other comments
			continue
		if l == None or len(l) < 1 or l[0] == '#':
			continue
		if l[0]== '[' and l !=  "[Desktop Entry]":
			active = False
			continue
		# else
		eqi = l.split('=')
		if len(eqi) < 2:
			print "Error: Invalid .desktop line'" + l + "'"
			continue
		# Check what it is ...
		if eqi[0] == "Name":
			this.addName(eqi[1])
		elif eqi[0] == "Comment":
			this.addComment(eqi[1])
		elif eqi[0] == "Exec":
			this.addExec(eqi[1])
		elif eqi[0] == "Icon":
			this.addIcon(eqi[1])
		elif eqi[0] == "Terminal":
			this.addTerminal(eqi[1])
		elif eqi[0] == "Type":
			if eqi[1] != "Application":
				continue
			this.addType(eqi[1])
		elif eqi[0] == "Categories":
                        if eqi[1]=="":
                            eqi[1]="Utility"
			if eqi[1][-1] == ';':
				eqi[1] = eqi[1][0:-1]
			cats = []
			# DEBUG 
			dtCats = eqi[1].split(';')
			for cat in dtCats:
				result = process_category(cat,  cats)
			this.addCategories(cats)
		else:
			continue
	# add to catDict
	#this.dprint()
	if len(this.Categories) > 0:        # don't care about stuff w/o category
		for cat in this.Categories:
			catDict[cat].append(this)

categoryDict = {}

if __name__ == "__main__":


    print 'hi'

##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
#hier here adapted for cdepanel / cdetheme 

#in cdepanel.py
#GenDefaultDrawersAndLayout.generate(configdir,12)
def generate(scriptpath,nitems):

    print scriptpath

    # init the application group dict (which will contain list of apps)
    for appGroup in application_groups:
        categoryDict[appGroup] = []

    # now let's look  into the app dirs ...
    for appDir in applications_dirs:
        appDir += "/*.desktop"
        dtFiles = glob.glob(appDir)

        # process each .desktop file in dir
        for dtf in dtFiles:
            skipFlag = False
            for ifn in ignoreList:
                if dtf.find(ifn) >= 0:
                    skipFlag = True
            if skipFlag == False:
                process_dtfile(dtf,  categoryDict)


    #EXTRACT allapps DICT I NEED FROM THIS SCRIPT
    #and write to 'allaps' for reference
    allapps={}

    allappsfullpath=os.path.join(scriptpath,'allapps')
    with open(allappsfullpath,'w') as f:
        appGroupLen = len(application_groups)
        for ag in range(appGroupLen ):
            catList = categoryDict[application_groups[ag]]
            if len(catList) < 1:
                continue                # don't create empty menus
            group=application_groups[ag]
            f.write(group)
            f.write('\n')
            allapps[group]=[]
            for app in catList:
                f.write(app.fileName)
                f.write('\n')
                allapps[group].append(app.fileName)

    #allaps contains all found apps in freedesktop categories defined above

    #in preferredapps: put categories (or some of them) and apps (or some of them)
    #   in the preferred order to be displayed, if found. Eg we want gimp first and
    #   not the app 'hp04bla_register_printer_func_wifi_autothinge_incomprehensible_spaghetti'
    #   Just copy&paste the preferredapps from 'allaps' in the right order
    preferredappsfullpath=os.path.join(scriptpath,'preferredapps')
    with open(preferredappsfullpath) as f:lines=f.read().splitlines() 

    #read preferredapps into hash preferredapps[Category][i]=/desktopentry/path/bla.desktop
    preferredapps={}
    currentkey=''
    for l in lines:
        if re.search('/',l):
            preferredapps[currentkey].append(l)
        else:
            currentkey=l
            preferredapps[currentkey]=[]

    #make hash 'final' with all apps, but put preferred apps first
    #hm hm if preferredapps are not found, they should be removed for different system
    preferredkeys=preferredapps.keys()
    final={}
    for key in allapps:
        #print key
        final[key]=[]
        if key in preferredkeys:
            #all apps present on system
            l1=allapps[key] 
            l2=[]
            #only use preferred apps that are present onsystem
            for l in preferredapps[key]:
                if l in l1:
                    l2.append(l)
            #unimportant apps
            l1minusl2=[x for x in l1 if x not in l2]
            #put the preferred apps first
            final[key]+=l2
            final[key]+=l1minusl2
        else:
            final[key]=allapps[key]

    #chomped, dont want more than this in a drawer
    finalchomped={}
    nmax=nitems-2
    for key in final:
        finalchomped[key]=[]
        n=0
        for i in final[key]:
            finalchomped[key].append(i)
            if n>nmax:break
            n+=1

    #reverse, the most important one must be on the bottom of the drawer
    #thats were the mouse pointer is at opening time
    nmax=nitems-2
    for key in finalchomped:
        #drawerfile='drawers/'+key
        drawerfile=os.path.join('drawers',key)
        drawerfilefullpath=os.path.join(scriptpath,drawerfile)
        with open(drawerfilefullpath,'w') as f:
            n=0
            for i in reversed(finalchomped[key]):
                f.write(i)
                f.write('\n')
                if n>nmax:break
                n+=1

    #/..../.desktop Drawer
    def drawerentry(key): return finalchomped[key][0]+' '+key
    def addentry(entry):
        f.write(entry)
        f.write('\n')

    userhome=os.path.expanduser("~")
    localappdir=userhome+'/.local/share/applications'

    #here1

    #defaultlayoutfile='defaultlayout'
    defaultlayoutfile=os.path.join(scriptpath,'layout')
    with open(defaultlayoutfile,'w') as f:
        addentry('clock NOAPP NODRAWER')
        addentry('date '+drawerentry('Office'))
        addentry('launcher '+localappdir+'/cdemotif-file-manager.desktop FileManager')
        addentry('launcher '+drawerentry('TerminalEmulator'))
        addentry('launcher '+drawerentry('Internet'))
        addentry('workspacebuttons NOAPP NODRAWER')
        addentry('launcher '+localappdir+'/cdemotif-printer.desktop System')
        #the cdemotif*.desktop are desktopentries pointing other apps,
        #but these will display with different icon (original cde icons) in the panel
        #see ~/.local/share/applications
        addentry('launcher '+localappdir+'/cdemotif-settings.desktop DesktopSettings')
        addentry('launcher '+localappdir+'/cdemotif-appfinder.desktop Utilities')
        addentry('launcher '+localappdir+'/cdemotif-help.desktop Documentation')
        addentry('launcher '+drawerentry('Multimedia'))




