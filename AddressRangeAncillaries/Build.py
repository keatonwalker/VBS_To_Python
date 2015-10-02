'''
Builds the Address range Splitter tool
Created on May 7, 2014

@author: kwalker
'''
import os, shutil, time

startTime = time.time()
currentTime = time.time()

srcDir = os.path.join(os.path.dirname(__file__), os.pardir, "AddressRangeSplitterTool")
ancillaryDir = os.path.dirname(__file__)
dstDir = os.path.join(os.path.dirname(__file__), os.pardir, r"Install_Files\AddressRangeSplitter")

if os.path.exists(dstDir):
    shutil.rmtree(dstDir)
    
os.mkdir(dstDir)

ancillaryFiles = ["Address Range Tool.tbx"]
for f in ancillaryFiles:
    shutil.copy(os.path.join(ancillaryDir, f), os.path.join(dstDir, f))

scriptFiles = []
for f in scriptFiles:
    shutil.copy(os.path.join(srcDir, f), os.path.join(dstDir, f))

print "Build Complete"
print
print "-- Remember to import script into tool --"
