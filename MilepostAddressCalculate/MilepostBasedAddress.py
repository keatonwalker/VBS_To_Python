'''
Created on Aug 15, 2013

Tool to calculate a milepost based address.

@author: kwalker
'''
import arcpy

class MilepostBasedAddress (object):
    #_inputRoad = ""
    
    _fromMPAddress = "FMPADR"
    _toMPAddress = "TMPADR"
    _fromMilePost = "DOT_F_MILE"
    _toMilePost = "DOT_T_MILE"
    _leftFromAddress = "L_F_ADR"
    _rightFromAddress = "R_F_ADR"
    _leftToAddress = "L_T_ADR"
    _rightToAddress = "R_T_ADR"
    
    def _deleteIfExists(self, featureName):
        if arcpy.Exists(featureName):
            arcpy.Delete_management(featureName)
    
    
    def calculateMilePostToAddress(self, inputRoad):
        ###What about None's???
        cursorFields = [self._fromMPAddress, 
                        self._toMPAddress, 
                        self._fromMilePost, 
                        self._toMilePost, 
                        self._leftFromAddress, 
                        self._rightFromAddress, 
                        self._leftToAddress, 
                        self._rightToAddress]
        roadCursor = arcpy.UpdateCursor(inputRoad)
        for row in roadCursor:
            print row.getValue(self._fromMilePost)
            print row.getValue(self._toMilePost)
            if row.getValue(self._fromMilePost) < row.getValue(self._toMilePost):
                row.setValue(self._fromMPAddress, row.getValue(self._fromMilePost) * 1000)
                row.setValue(self._toMPAddress, row.getValue(self._toMilePost) * 1000)
                print "<"
            elif row.getValue(self._fromMilePost) > row.getValue(self._toMilePost):
                row.setValue(self._fromMPAddress, row.getValue(self._toMilePost) * 1000)
                row.setValue(self._toMPAddress, row.getValue(self._fromMilePost) * 1000)
                print ">"
            
            if row.getValue(self._fromMPAddress) == None:#int(self._fromMPAddress) % 2 == 0:
                print "Howdy fucker"
   
                
if __name__ == "__main__":
    inputRoad = r"C:\KW_Working\VB_to_Python\MilepostAddress\TestRoute.gdb\US_Route0006"
    milePostAdresser = MilepostBasedAddress()
    milePostAdresser.calculateMilePostToAddress(inputRoad)
    