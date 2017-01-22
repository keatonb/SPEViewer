#Open SPE files and display the frames.
#Allow users to write out timestamp CSV.

from __future__ import absolute_import, division
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
#import astropy.io.fits as fits
#import math
import sys
import os
#import time
#from astropy.stats import biweight_location, biweight_midvariance
#from photutils import daofind
import read_spe
from writetimestamps import writetimestamps

#stage variable tracks what the program should currently be doing
# 0 - Just initialized, waiting for SPE file
# 1 - SPE loaded.

global stage
stage = 0
        
class KFrameView(pg.ImageView):
    """This Image View widget can open and manipulate the SPE data
    
    This widget is aware of:
    the loaded filename
    the file data
    """
    def __init__(self):
        super(KFrameView, self).__init__()
        #Hide the stupid buttons    
        self.ui.roiBtn.hide()
        #self.ui.normBtn.hide()  
        #self.timeLine.si


    #Variables this object owns
    #Filename
    filename = ''

    #We track two versions of the image:
    # img - the original, for measurement
    # displayimg - modified for display
    img = np.zeros(0)  
    displayimg = np.zeros([0,0,0])
    
    # SPE - load SPE file
    spe = np.zeros(0)
    
    numframes=0
    
    times=0
        
    def loadSPE(self):  #for SPE
        """
        Loads data from SPE file
        
        Checks a lot of details about the SPE file, including:
        - Whether footer exists (if not, run in 'online' mode)
        - Number of frames
        - Exposure time
        """
        global stage
        stage=1        
        
        self.spe = read_spe.File(self.filename)
        (frame1,time1) = self.spe.get_frame(0)
        self.img = [np.transpose(frame1)]
        self.times = [time1]
        for i in range(1,self.spe.get_num_frames()):
            (thisframe,thistime) = self.spe.get_frame(i)
            self.img.append(np.transpose(thisframe))
            self.times.append(thistime)
        self.img=np.array(self.img)
        self.numframes = self.spe.get_num_frames()
        
        self.makeDisplayImage()
        self.spe.close()
        
    def makeDisplayImage(self):
        displayimg = np.copy(self.img)
        
        #Insert one 0-value pixel to control minimum
        for i in range(displayimg.shape[0]):
            displayimg[i,0,0]=0
            imgvals = displayimg[i].flatten()
            #replace everything above 99%tile
            #don't do calulcations on this adjusted array!!!
            img99percentile = np.percentile(imgvals,99)
            displayimg[i][displayimg[i] > img99percentile] = img99percentile
            #make color
        #self.displayimg=np.rollaxis(np.array(displayimg),0,1)
        self.displayimg=np.array(displayimg)
        
        
    #show the image to the widget
    def displayFrame(self,autoscale=False):
        """Display an RBG image
        Autoscale optional.
        Return nothing.
        """
        if autoscale:
            thisimg=self.displayimg[self.currentIndex]
            lowlevel=np.min(thisimg[thisimg > 0])
            highlevel=np.max(thisimg)-1
            self.setImage(self.displayimg,autoRange=True,levels=[lowlevel,highlevel])
        else:
            self.setImage(self.displayimg,autoRange=False,autoLevels=False)
            
    #print frame number on change

    def writeTimes(self):
        self.spe = read_spe.File(self.filename)
        writetimestamps(self.spe,self.filename)
        fpath_csv = os.path.splitext(self.filename)[0]+'_timestamps.csv'
        return fpath_csv

class KMainWindow(QtGui.QMainWindow):
    """Main window with menu settings
    
    The 'K' is for Keaton    
    """
    
    def __init__(self):
        super(KMainWindow, self).__init__()
        
        #self.frameview.file='SDSSJ1618+3854.spe'
        #self.frameview.loadSPE()
        #self.frameview.displayFrame(autoscale=True)
        #self.frameview.getImageItem().mouseClickEvent = self.frameview.click  

        self.initUI()
        
    def initUI(self):
        
        self.frameview = KFrameView()
        self.setCentralWidget(self.frameview)
        
        #Menu details
        openFile = QtGui.QAction('&Open SPE', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)
        
        writeTime = QtGui.QAction('&Write timestamps', self)
        writeTime.setShortcut('Ctrl+W')
        writeTime.setStatusTip('Write timestamps')
        writeTime.triggered.connect(self.writeTimes)
        
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(writeTime)
        
        #Status bar
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Load a SPE file.")
        
        
        self.setWindowTitle("SPEViewer")
        self.show()
        self.raise_()
        #self.showDialog()
        self.frameview.timeLine.sigPositionChanged.connect(self.updateStatus)
        
        self.statusbar.messageChanged.connect(self.updateStatusIdle)        
        
        #self.frameview.getImageItem().sigMouseHover.connect(self.mouseMoved)
        #self.frameview.getImageItem().mouseClickEvent = self.mouseMoved
        
    def updateStatus(self):
        #show current frame number in status bar 
        self.statusbar.showMessage("Current frame: "+str(self.frameview.currentIndex))
        
    def updateStatusIdle(self):
        #show current frame number in status bar 
        if self.statusbar.currentMessage() == '':
            self.statusbar.showMessage("Current frame: "+str(self.frameview.currentIndex))
        
    def clickImage(self,event):
        '''show coordinates clicked on for 5 seconds
        
        
        '''
        global stage
        if stage == 1: #test stage
            event.accept()  
            pos = event.pos()
            clickpos=[int(pos.x()),int(pos.y())]
            self.statusbar.showMessage("Clicked "+str(clickpos),5000)
        
    def showDialog(self):
        self.statusbar.showMessage("Load a SPE file.")
        fname = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                os.getcwd()))
        if fname != '' and fname[-4:]=='.spe':
            self.statusbar.showMessage("Loading SPE (this may take a moment)...")
            self.frameview.filename=os.path.abspath(fname)
            self.frameview.loadSPE()
            self.frameview.displayFrame(autoscale=True)
            self.statusbar.showMessage("SPE loaded.",5000)
            self.frameview.getImageItem().mouseClickEvent = self.clickImage
            self.updateStatus()
        
    def writeTimes(self):
        filecsv=self.frameview.writeTimes()
        self.statusbar.showMessage("Wrote "+filecsv,7000)
    


# Create app
app = QtGui.QApplication([])

## Create window
win = KMainWindow()
win.resize(500,450)
win.showDialog()


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
