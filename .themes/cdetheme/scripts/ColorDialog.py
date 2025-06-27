#!/usr/bin/python
# pyuic4 ui_ColorDialog.ui -o ui_ColorDialog.py
# 
# https://github.com/mattrobenolt/colors.py/blob/master/colors/base.py
#
import sys
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
from PyQt4 import QtGui,QtCore 
from PyQt4.QtCore import QString
import subprocess
import re
from functools import partial
from colors import hsv, hex
import Globals
#QTDESIGNER FILE DONT EDIT:
import ui_ColorDialog
import WorkspaceFuncs
import os
import time
from pprint import pprint
from MiscFun import *

class ColorPicker(QtGui.QColorDialog):
    def __init__(self, bgcol,parent=None):
        super(ColorPicker, self).__init__(bgcol,parent)
        self.show()
        #maybe use this later instead of direct fun call (but is slower apparently)
        self.connect(self,QtCore.SIGNAL('mouseReleased'),self.testFun)
    def testFun(self):
        print 'blabla use later'
    def mouseReleaseEvent(self,event):
        self.emit(QtCore.SIGNAL('mouseReleased'))
        #self.parent().colorPickerMouseReleased(event)
        super(ColorPicker, self).mouseReleaseEvent(event)

class ColorDialog(QtGui.QDialog, ui_ColorDialog.Ui_Dialog):
    def __init__(self,mainwindow):
        super(self.__class__, self).__init__()
        #from ui_ColorDialog:
        self.updateThemeDelay=100
        self.applyStyleSheetDelay=500
        self.setupUi(self)  
        self.mainwindow=mainwindow
        self.oldbgcol=None
        #must come before call to updateStyleSheet, var referenced there
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), "Colors")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), "Backdrops")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), "Desktop Theme")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), "Advanced")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "Help")
        self.tabWidget.setCurrentIndex(0)   
        #TAB 1 COLORS #############################################
        self.colorButton=[ self.colorbutton1, self.colorbutton2, self.colorbutton3, self.colorbutton4, 
            self.colorbutton5, self.colorbutton6, self.colorbutton7, self.colorbutton8 ]
        self.addPalettesToList()
        self.setCurrentPalettefileActiveInList()
        self.initialPaletteFile=self.mainwindow.opts.currentpalettefile
        self.backupPalette()
        self.listWidget.selectionModel().selectionChanged.connect(self.selectPalette)
        #the buttns
        self.pushButton.clicked.connect(self.newPalette)
        self.pushButton_3.clicked.connect(self.deletePalette)
        self.pushButton_2.clicked.connect(self.restorePalette)
        self.pushButton_13.clicked.connect(self.closeDialog)
        self.pushButton_14.clicked.connect(self.cancelCloseDialog)
        self.pushButton_4.clicked.connect(partial(self.modHSV,0.01,1,1))
        self.pushButton_5.clicked.connect(partial(self.modHSV,-0.01,1,1))
        self.pushButton_7.clicked.connect(partial(self.modHSV,0,1.1,1))
        self.pushButton_9.clicked.connect(partial(self.modHSV,0,0.9,1))
        self.pushButton_6.clicked.connect(partial(self.modHSV,0,1,1.05))
        self.pushButton_8.clicked.connect(partial(self.modHSV,0,1,0.95))
        self.pushButton_12.clicked.connect(partial(self.setNColors,4))
        self.pushButton_11.clicked.connect(partial(self.setNColors,8))
        self.pushButton_10.clicked.connect(partial(self.setPanelColor,8))
        self.pushButton_15.clicked.connect(partial(self.setPanelColor,5))
        #set action edit color N for the color buttons
        i=1
        for b in self.colorButton:
            b.clicked.connect(partial(self.editColor,i))
            i+=1
        #TAB 2 BACKDROPS #############################################
        self.wsColorButton=[ self.wscolorbutton1, self.wscolorbutton2, self.wscolorbutton3, self.wscolorbutton4, 
            self.wscolorbutton5, self.wscolorbutton6, self.wscolorbutton7, self.wscolorbutton8 ]
        i=1
        for b in self.wsColorButton:
            b.clicked.connect(partial(self.setColorsetForCurrentWorkspace,i))
            i+=1
        self.addBackdropsToList()
        self.blockSetCurrentBackdropfileActiveInList=False
        self.setCurrentBackdropfileActiveInList()
        #update in case of workspace switch
        self.yetimer=QtCore.QTimer()
        self.yetimer.timeout.connect(self.setCurrentBackdropfileActiveInList)
        self.yetimer.start(300)
        self.listWidget_2.selectionModel().selectionChanged.connect(self.selectBackdrop)

        #TAB 3 DESKTOP THEME #############################################
        #apply xfce theme or use standalone panel
        self.pushButton_16.clicked.connect(partial(self.setEnvironment,''))
        self.pushButton_17.clicked.connect(partial(self.setEnvironment,'xfce'))
    
        self.spinBox.setProperty("value", self.mainwindow.opts.internalborderwidth)
        self.spinBox.valueChanged.connect(self.spinBorderWidth)
        self.spinBox_2.setProperty("value", self.mainwindow.opts.internaltitleheight)
        self.spinBox_2.valueChanged.connect(self.spinTitleHeight)

        ##################################################################
        #self.mainwindow.readPaletteFile()#hmmm..??
        self.updateStyleSheet()
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)

        #TAB 5 EDIT CONFIG ##############################################

        self.loadConfigFile()
        self.pushButton_18.clicked.connect(partial(self.saveConfigFileAndRestart))
        self.pushButton_19.clicked.connect(self.cancelCloseDialog)
        self.pushButton_20.clicked.connect(self.restoreConfigFileToDefault)
        self.pushButton_21.clicked.connect(self.clearIconCache)

        #TAB 6 HELP ##############################################
        configstr=QString("")
        #self.helpColorDialog = QtGui.QPlainTextEdit(self.tab)
        self.helpColorDialog.setReadOnly(True)
        self.helpColorDialog.appendPlainText(configstr)
        with open(Globals.helptxt) as f:lines=f.read()
        self.helpColorDialog.appendPlainText(lines)
        self.helpColorDialog.moveCursor(QtGui.QTextCursor.Start)

        #self.openSettings.clicked.connect(self.mainwindow.openConfigDialog)
        #self.closeHelp.clicked.connect(self.close)


    def restoreConfigFileToDefault(self):
        configfile=Globals.configfile
        defaultconfigfile=Globals.configdir+'/config.default'
        print defaultconfigfile
        if os.path.exists(defaultconfigfile):
            cmd=""" cp {defaultconfigfile} {configfile} """.format(**locals())
            print cmd
            execWSysLibsStdO(cmd)
        self.loadConfigFile()
        return

    def loadConfigFile(self):
        configstr=QString("")
        #self.plainTextEdit.appendPlainText(configstr)
        with open(Globals.configfile) as f:lines=f.read()
        self.plainTextEdit.setPlainText(lines)
        self.plainTextEdit.moveCursor(QtGui.QTextCursor.Start)
        
    def saveConfigFileAndRestart(self):
        configfile=Globals.configfile
        backup=Globals.configfile+'.backup'
        cache=Globals.cache

        cmd=""" cp {configfile} {backup}""".format(**locals())
        print cmd
        execWSysLibsStdO(cmd)

        newconfigstr=self.plainTextEdit.toPlainText()
        with open(configfile, 'w') as f:
                f.write(newconfigstr)

        #DIT WERKT NIET MET DEZE2, WAAROM?
        #execWSysLibsNonBlckStdOE(sys.argv[0])
        #execWSysLibNonBlock(sys.argv[0])
        subprocess.Popen(sys.argv[0])
        os.kill(os.getpid(), signal.SIGINT)
        sys.exit(0)

    def clearIconCache(self):
        print "Emptying icon cache. At next startup, icons will be refreshed"
        cache=Globals.cache
        cmd="""rm -rf {cache}/* """.format(**locals())
        print cmd
        execWSysLibsStdO(cmd)

    def spinTitleHeight(self):
        self.mainwindow.opts.internaltitleheight=self.spinBox_2.value()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        self.mainwindow.saveAll()
    def spinBorderWidth(self):
        self.mainwindow.opts.internalborderwidth=self.spinBox.value()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        self.mainwindow.saveAll()
    def setColorsetForCurrentWorkspace(self,colorset):
        currentworkspace=WorkspaceFuncs.getCurrentWorkspace()
        self.mainwindow.setWorkspaceColor(currentworkspace,colorset)
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        self.mainwindow.saveAll()#voor opts.currentpalettefile
    def setEnvironment(self,environment):
        if environment=='xfce':
            self.mainwindow.opts.themeGtk=True
            self.mainwindow.opts.themeBackdrops='xfce'
            self.mainwindow.opts.themeWindecs='xfce'
        else:
            self.mainwindow.opts.themeGtk=False
            self.mainwindow.opts.themeBackdrops=''
            self.mainwindow.opts.themeWindecs=''

        self.mainwindow.saveAll()
    def setPanelColor(self,N):
        self.mainwindow.setPanelColor(N)
    def setNColors(self,N):
        self.mainwindow.setNColors(N)
        self.updateStyleSheet()
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)
    #modify hsv of all bgcolors
    def modHSV(self,deltah,deltas,deltav):
        #for i in range(self.mainwindow.opts.ncolors):
        for i in range(Globals.ncolorstosave):
            n=i+1
            col=Globals.colorshash['bg_color_'+str(n)]
            col=re.sub('#','',col)
            colhsv=hex(col).hsv
            hue=colhsv.hue+deltah
            saturation=colhsv.saturation*deltas
            value=colhsv.value*deltav
            if hue>1:hue=hue-1
            if hue<0:hue=1-hue
            if saturation>1:saturation=1
            if value>1:value=1
            colhexmod= '#'+str(hsv(hue,saturation,value).hex)
            Globals.colorshash['bg_color_'+str(n)]=colhexmod
        self.updateStyleSheet()
        self.mainwindow.savePalette()
        self.mainwindow.readPaletteFile()
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
    #load backdropdir all .pm files, remove extension and put in list
    def loadBackdropDir(self,directory):
        cmd='ls'+' '+directory+'/*.pm'
        output=execWSysLibsStdO(cmd)
        lines=output.splitlines() #array with elements=lines
        bds=[]
        for l in lines:
            basename=os.path.basename(l)
            basenamenoext, file_extension = os.path.splitext(basename)
            bds.append(basenamenoext)
        return bds
    def addBackdropsToList(self):
        backdrops=self.loadBackdropDir(Globals.backdropdir)
        for p in backdrops:
            self.listWidget_2.addItem(p)
    #this must be done every N ms in case of workspace switch
    def setCurrentBackdropfileActiveInList(self):
        if self.blockSetCurrentBackdropfileActiveInList:return
        currentworkspace=WorkspaceFuncs.getCurrentWorkspace()
        currentbackdrop=self.mainwindow.getBackdropForWorkspaceNr(currentworkspace)
        for i in range(self.listWidget_2.count()):
            it=self.listWidget_2.item(i)
            if it.text()==currentbackdrop:
                self.listWidget_2.setCurrentItem(it)
    def addPalettesToList(self):
        #add palttefiles to the list widgets
        for p in Globals.palettes:
            self.listWidget.addItem(p)
    def setCurrentPalettefileActiveInList(self):
        for i in range(self.listWidget.count()):
            it=self.listWidget.item(i)
            if it.text()==self.mainwindow.opts.currentpalettefile:
                self.listWidget.setCurrentItem(it)
    def deletePalette(self):
        oldfullfilename=Globals.palettedir+'/'+self.mainwindow.opts.currentpalettefile
        oldpalettefile=self.mainwindow.opts.currentpalettefile
        messagestr="""Delete palette {oldpalettefile}?""".format(**locals())
        message= QtGui.QMessageBox()
        ret = message.question(self,'', messagestr, message.Yes | message.No)
        if ret == message.No:return
        self.mainwindow.switchPalette(1)
        cmd="""rm {oldfullfilename} """.format(**locals())
        output=execWSysLibsStdO(cmd)
        Globals.palettes=self.mainwindow.opts.loadPaletteDir(Globals.palettedir)
        self.setCurrentPalettefileActiveInList()
        #wtf listWidget.clear calls selectPalette for some reason and then pick the wrong palette. so before clear set the right palette select active first
        self.listWidget.clear()
        self.addPalettesToList()
        self.setCurrentPalettefileActiveInList()
    def newPalette(self):
        #Mysterious magic formula code 
        text, ok = QtGui.QInputDialog.getText(self, 'Create new palette', 'New palette name:',QtGui.QLineEdit.Normal,self.mainwindow.opts.currentpalettefile)
        if not ok: return
        #todo add validate here
        oldfilename=Globals.palettedir+'/'+self.mainwindow.opts.currentpalettefile
        newfilename=Globals.palettedir+'/'+text
        cmd="""cp {oldfilename} {newfilename}  """.format(**locals())
        print cmd
        print 'text '+str(text)#__debug
        output=execWSysLibsStdO(cmd)
        Globals.palettes=self.mainwindow.opts.loadPaletteDir(Globals.palettedir)
        self.listWidget.clear()
        self.addPalettesToList()
        self.mainwindow.opts.currentpalettefile=text
        self.setCurrentPalettefileActiveInList()
    #when list item=palettefile clicked, set current palette to this and update palette etc
    #when is this damn thing being calle dmore????
    #IT IS ALSO BEING CALLED ON WORKSPACE CHANGE EVEN WHEN THE DIALOG IS ALREADY CLOSED HMMM
    def selectBackdrop(self):
        #prevent updating the listview to the current workspace after selecting a new one
        self.blockSetCurrentBackdropfileActiveInList=True
        currentworkspace=WorkspaceFuncs.getCurrentWorkspace()
        cur=self.listWidget_2.currentItem()
        selectedbackdrop=str(cur.text())
        self.mainwindow.setBackdropForWorkspaceNr(currentworkspace,selectedbackdrop)
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        #self.mainwindow.saveAll()#voor opts.currentpalettefile
        #re-enable auto updating the list
        self.blockSetCurrentBackdropfileActiveInList=False
    def selectPalette(self): 
        #ok what is the order to make this quickest update the dialog
        cur=self.listWidget.currentItem()
        self.backupPalette()
        self.mainwindow.opts.currentpalettefile=str(cur.text())
        self.mainwindow.readPaletteFile()
        self.updateStyleSheet()
        #todo why need delay=500!? stylesheet update to wrong color?
        #aha yes 500 del also doesnt work if not updateXfceTheme so stylesheet
        #is wrong(ie picks up colors from gtkrc id updateXfceTheme, but not from stylesheeeeeet)
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)#not needed anymore? Yes for updating gtkrc change ... 
        #todo #scrollbar en tab style wordt nog niet meteen geupdate warrom???  #met stylesheet updat kan wel kleur direct aanpassen
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        self.mainwindow.saveAll()#voor opts.currentpalettefile
    #save  a copy of the palette file to be able to revert changes after editing
    def backupPalette(self):
        filename=Globals.palettedir+'/'+self.mainwindow.opts.currentpalettefile
        tmpfilename=os.path.join(Globals.tmpdir,self.mainwindow.opts.currentpalettefile)
        cmd=""" cp {filename} {tmpfilename} """.format(**locals())
        output=execWSysLibsStdO(cmd)
        print output
    def editColor(self,colnr):
        print 'def editColor(self,colnr):'
        #init color for ColorPicker
        bgcol=Globals.colorshash['bg_color_'+str(colnr)]
        self.oldbgcol=bgcol
        print 'self.oldbgcol '+str(self.oldbgcol)#__debug
        #newcol = QtGui.QColorDialog.getColor(QtGui.QColor(bgcol), self)
        colorpicker = ColorPicker(QtGui.QColor(bgcol), self)
        #colorpicker.currentColorChanged.connect(self.colorChanged)
            #hmm how does this actually work.... signal currentColorChanged passes arg 'col' to colorChanged 
            #but apparently I can still pass an additional argument. This only works if 'col' is the last arg of colorChanged
        colorpicker.currentColorChanged.connect(partial(self.colorChanged,colnr))
        colorpicker.rejected.connect(partial(self.cancelColorPicker,colnr))
    def cancelColorPicker(self,colnr):
        #restore edited color to previous value
        Globals.colorshash['bg_color_'+str(colnr)]=self.oldbgcol
        self.updateStyleSheet()
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)#not needed anymore Yes for updating gtkrc change ... OMGGGG
        #save the palette with just this color restored to the previous one. Other colors can still have changed values
        self.mainwindow.savePalette()
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)
        self.mainwindow.readPaletteFile()
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
    #quick color changes, as long as mouse button is pressed/dragged
    def colorChanged(self,colnr,col):
        #TODO HERE ALSO GLOBALS.COLORS TO WORK. BUT BETTER MOVE FROM GLOBALS.COLORS TO GLOBALS.COLORHASH EVERYWERHE
        Globals.colorshash['bg_color_'+str(colnr)]=col.name()
        self.updateStyleSheet()
        self.uc8=QtCore.QTimer()
        self.uc8.setSingleShot(True)
        self.uc8.timeout.connect(self.updateChangedColor)
        self.uc8.start(500)
    #slow color changes, when button is releasedhmmm something changed
    def updateChangedColor(self):
        self.mainwindow.savePalette()
        #self.delayedApplyStyleSheet(delay=500)#not needed anymore?
        self.mainwindow.readPaletteFile()
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
    #NO USE FOR NOW TRY UC8 TIMER INSTEAD
    #NO USE FOR NOW TRY UC8 TIMER INSTEAD
    #NO USE FOR NOW TRY UC8 TIMER INSTEAD
    #def colorPickerMouseReleased(self,event):
        #self.mainwindow.savePalette()
        #self.delayedApplyStyleSheet(delay=500)#not needed anymore?
        #self.mainwindow.readPaletteFile()
        #self.mainwindow.initUpdateResourceImgs()
        #self.mainwindow.prepareBackDrops()
        #self.mainwindow.theme.updateTheme()
            #KLOPT OOK NIET HELEMAAL: COLORPICKER VERANDERT BG KLEUR VAN EEN SET, MAAR DE TS BS ETC WORDEN 
            #NIET BEREKEND, DAT DOET MOTIFCOLORS, MAAR ALLEEN VAN BESTAND VAN DISK. DUS OF MOTIFCOLORS
            #OMZETTEN NAAR PY OF SCHRIJVEN NAAR DISK? KAN NU BIJV NIET ACHTERGROND IN GAAN VULLEN MET
            #GEUPDATE GLOBALSCOLORSHASH OMDAT DIE ALLEEN BG GEUPDATEHEEFT
            #DUS EIGL MOET BIJ HET BEWEGEN VAN DE COLORPICKER NIET ALLEEN BG WORDEN GEUPDATE MAAR OOK TS BS ETC
            #EN KAN ALLEEN ALS MOTIFCOLORS IN PY ZIT
            #this is reading from disk so color changed here cant be effected right now... hm   
            #so either save to disk after mouseup or 
            # ummm.. yes
    def restorePalette(self):
        filename=Globals.palettedir+'/'+self.mainwindow.opts.currentpalettefile
        #copy back old paletefile
        tmpfilename=os.path.join(Globals.tmpdir,self.mainwindow.opts.currentpalettefile)
        cmd=""" cp {tmpfilename} {filename} """.format(**locals())
        output=execWSysLibsStdO(cmd)
        self.mainwindow.readPaletteFile()
        self.updateStyleSheet()
        self.delayedApplyStyleSheet(delay=self.applyStyleSheetDelay)
        #todo #scrollbar en tab style wordt nog niet meteen geupdate warrom???  #met stylesheet updat kan wel kleur direct aanpassen
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
    def closeEvent(self,event):
        #deletelater is needed because without the dialog keeps active in the background
        #(problem with update theme keeping beeing called)
        self.setParent(None)
        self.deleteLater()
    def closeDialog(self):
        #save stuff here?
        self.close()
    def cancelCloseDialog(self):
        self.mainwindow.opts.currentpalettefile=self.initialPaletteFile
        self.mainwindow.readPaletteFile()
        self.mainwindow.initUpdateResourceImgs()
        self.mainwindow.theme.updateTheme(delay=self.updateThemeDelay)
        self.closeDialog()
    def delayedApplyStyleSheet(self,delay=500):
        self.xY5=QtCore.QTimer()
        self.xY5.setSingleShot(True)
        self.xY5.timeout.connect(self.applyStyleSheet)
        self.xY5.start(delay)
    #gtkrc2 is not picked up correctly by QT 'GTK+' style
    def applyStyleSheet(self):
        def recursive_set(parent):
            for child in parent.findChildren(QtCore.QObject):
                try:
                    child.style().unpolish(self)
                    child.style().polish(self)
                    child.update()
                except: pass
                recursive_set(child)
        recursive_set(self)
    def updateStyleSheet(self):
        for i in range(Globals.ncolorstosave):
            n=i+1
            bgcol=Globals.colorshash['bg_color_'+str(n)]
            b=self.colorButton[i]
            b.setStyleSheet("""
                 background-color:{bgcol};
            """.format(**locals()))
            b=self.wsColorButton[i]
            b.setStyleSheet("""
                 background-color:{bgcol};
            """.format(**locals()))
        background6=Globals.colorshash['bg_color_6']
        foreground6=Globals.colorshash['fg_color_6']
        background4=Globals.colorshash['bg_color_4']
        foreground4=Globals.colorshash['fg_color_4']
        ts_gen=Globals.colorshash['ts_color_6']
        bs_gen=Globals.colorshash['bs_color_6']
        fg_gen=Globals.colorshash['fg_color_6']
        bg_gen=Globals.colorshash['bg_color_6']
        sel_gen=Globals.colorshash['sel_color_6']
        font=Globals.font
        fontStyle=Globals.fontStyle
        fontSize=Globals.fontSize
        #updated gtk styles dont for some reason take effect for Qt GTK+ style so hmmmf do manually
        #at least for this window
        #how give everything the same color?
        #20221114 fonts erbij gezet
        #added some styles for qt4, because they dont render on qt5 systems
        #hierx
        imgbitpng=Globals.themedir+ "/img2/colorset6/frameStandAlone.png"       
        styles="""
            * {{ 
            background-color:{background6}; color:{foreground6};
            font-family:"{font}"; font-size:{fontSize}px;
            }}

            QTabBar::tab {{
                padding: 5px;
                margin: 1px;
                color:			{fg_gen};
                background-color: 	{sel_gen};
                border-style:solid;
                border-width:1px;
                border-top-color:	{ts_gen};
                border-left-color:	{ts_gen};
                border-right-color:	{bs_gen};
                border-bottom-color:	{bs_gen};
	        outline-offset: 2px;
             }}

            QTabBar::tab::selected {{
                padding: 5px;
                margin: 1px;
                color:			{fg_gen};
                background-color: 	{bg_gen};
                border-style:solid;
                border-width:1px;
                border-top-color:	{ts_gen};
                border-left-color:	{ts_gen};
                border-right-color:	{bs_gen};
                border-bottom-color:	{bs_gen};
             }}

            QPushButton {{
                padding: 5px;
                margin: 1px;
                color:			{fg_gen};
                border-style:solid;
                border-width:1px;
                border-top-color:	{ts_gen};
                border-left-color:	{ts_gen};
                border-right-color:	{bs_gen};
                border-bottom-color:	{bs_gen};
             }}

            QPushButton:pressed {{
                padding: 5px;
                margin: 1px;
                color:			{fg_gen};
                border-style:solid;
                border-width:1px;
                border-top-color:	{bs_gen};
                border-left-color:	{bs_gen};
                border-right-color:	{ts_gen};
                border-bottom-color:	{ts_gen};
             }}


            QtGui.QWidget {{ background-color:{background6}; color:{foreground6};}}
            QObject {{ background-color:{background6}; color:{foreground6};}}
            QGridLayout {{ background-color:{background6}; color:{foreground6};}}
            QTabWidget {{ background-color:{background6}; color:{foreground6};}}
            QScrollBar {{ background-color:{background6}; color:{foreground6};}}
            QSlider {{ background-color:{background6}; color:{foreground6};}}
            QWidget {{ background-color:{background6}; color:{foreground6};}}
            QListWidget {{ background-color:{background4}; color:{foreground4};}}
            QListWidgetItem {{ background-color:{background4}; color:{foreground4};}}

            QFrame {{
                    border-style: solid;
                    border-color: {ts_gen};
                    border-width:1px;
                    }}


            QTabWidget {{
                    border-style:solid;
                    border-width:0px;
            }}
            QLabel {{
                    border-style:solid;
                    border-width:0px;
            }}

        """.format(**locals())

        self.setStyleSheet(styles)

            #this simply turns the entire slider into a single block of color
            #QSlider::groove:horizontal {{background-color:red;}}
            #QSlider::handle:horizontal {{background-color:green; height:10px; width:10px;}}
        #for i in range(self.mainwindow.opts.ncolors):

        #20221114 do this for now to also apply qt4 style chagnes to popup menu of panel
        #put this in one file later 
        Globals.cdepanel.updateStyleSheet();
def main():

    print 'debugme'


if __name__ == '__main__':           
    main()                          
