'''
Created on Jul 30, 2013

@author: kwalker
'''
import arcpy, time
import AddressSplitterTool

def _resetTestRoads(roadsBase, roads):
    arcpy.Delete_management(roads)
    arcpy.CopyFeatures_management(roadsBase, roads)
    

if __name__ == "__main__":
    
    roadsBase = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\AddressSplitterTestData_Full.gdb\StreetsTestData_Base"
    roads = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\AddressSplitterTestData_Full.gdb\StreetsTestData"
    boundaries = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\AddressSplitterTestData_Full.gdb\PolygonTestData"
    outputDir = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\testOutputs\filterTestOut3"
    
    _resetTestRoads(roadsBase, roads)
#     startTime = time.time()
#     splitter = AddressSplitterTool.AddressRangeSplitter(roads, boundaries, outputDir)
#     splitter.splitAddressRanges()
#     print "Total mins: {}".format((time.time() - startTime)/60)