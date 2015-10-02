import arcpy, os, NewRangeAssignment

class AddressRangeSplitter (object):
    _wholeRoads = ""
    _boundaries = ""
    _outputDirectory = ""
    _tempGDBPath = ""
    _tempGDBName = "tempGDB.gdb"
    
    def __init__ (self, roadsPath, boundariesPath, outputDirectoryPath):
        self._wholeRoads = roadsPath
        self._boundaries = boundariesPath
        self._outputDirectory = outputDirectoryPath
        self._tempGDBPath = os.path.join(self._outputDirectory, self._tempGDBName)
        
    def _addFieldsToIdentityRds(self, identityFeature, isStartField, wholeLengthField, errorField, errorNotesField):
        arcpy.AddField_management (identityFeature, isStartField, "SHORT")
        arcpy.AddField_management(identityFeature, wholeLengthField, "DOUBLE")
        arcpy.AddField_management (identityFeature, errorField, "SHORT")
        arcpy.AddField_management(identityFeature, errorNotesField, "TEXT", field_length = 75)
        
    def _getInputRoadOidName(self):
        desc = arcpy.Describe(self._wholeRoads)
        return desc.OIDFieldName
        
    def _getFrequencyFieldName(self):
        desc = arcpy.Describe(self._wholeRoads)
        freqFieldName = "FID_{}".format(desc.baseName)
        return freqFieldName
        
    def _deleteIfExists(self, featureName):
        if arcpy.Exists(featureName):
            arcpy.Delete_management(featureName)
    
    def _deleteTempLayers(self, tempLayersList):
        for layer in tempLayersList:
            self._deleteIfExists(layer)
            
    def _copyErrorFeatures(self, identityFeature, errorField, newErrorLayerName):
        self._deleteIfExists("errorRecord")
        arcpy.MakeFeatureLayer_management(identityFeature,"errorRecord", """"{}" = 1""".format(errorField))
        arcpy.CopyFeatures_management("errorRecord", newErrorLayerName)
        
    def _expandErrorFlagAcrossIdNumbers(self,identityFeature, errorField, errorNotesField, frequencyIdField):
        with arcpy.da.SearchCursor(identityFeature, [frequencyIdField, errorField, errorNotesField], """"{}" = 1""".format(errorField)) as cursor:
            for row in cursor:
                self._deleteIfExists("errorIdentityFeature")
                arcpy.MakeFeatureLayer_management(identityFeature,
                                                   "errorIdentityFeature", """"{}" = {}""".format(frequencyIdField, row[0]))
                arcpy.CalculateField_management("errorIdentityFeature", errorField, row[1])
                arcpy.CalculateField_management("errorIdentityFeature", errorNotesField, "\"{}\"".format(row[2]))
                
    def _updateFeatures(self, identityFeature, frequencyField, wholeLengthField, errorField):
        self._deleteIfExists("identityfeatureToAdd")
        arcpy.MakeFeatureLayer_management(identityFeature, "identityfeatureToAdd",
                                           """"{}" IS NOT NULL AND "{}" IS NULL""".format(wholeLengthField, errorField))
        with arcpy.da.SearchCursor("identityfeatureToAdd", [frequencyField]) as cursor:
            for row in cursor:
                self._deleteIfExists("wholeRoadToDelete")
                arcpy.MakeFeatureLayer_management(self._wholeRoads,
                                                   "wholeRoadToDelete", """"{}" = {}""".format(self._getInputRoadOidName(), row[0]))
                arcpy.DeleteFeatures_management("wholeRoadToDelete")
        
        
        arcpy.Append_management("identityfeatureToAdd", self._wholeRoads, "NO_TEST")
    
    
    def _transferInfoFromWholeToIdentity(self, IdNumber, identityFeature, isStartField, wholeLengthField, errorField, errorNotesField):
        
        with arcpy.da.SearchCursor(self._wholeRoads, ["SHAPE@"], """"{}" = {}""".format(self._getInputRoadOidName(), IdNumber)) as wholeRdCursor:
            for wholeRow in wholeRdCursor:
                with arcpy.da.UpdateCursor(identityFeature, ["SHAPE@", isStartField, wholeLengthField, errorField, errorNotesField], """"{}" = {}""".format(self._getFrequencyFieldName(), IdNumber)) as identityCursor:
                    for identityRow in identityCursor:
                        if identityRow[0].partCount > 1:
                            identityRow[3] = 1
                            identityRow[4] = "Not Updated: Road split into a multipart feature"
                            
                        if wholeRow[0].firstPoint.touches(identityRow[0]):
                            identityRow[1] = 1
                        
                        identityRow[2] = wholeRow[0].length
                        identityCursor.updateRow(identityRow)
    
    def _createTempGDB(self, gdbName):
        if arcpy.Exists(self._tempGDBPath):
            arcpy.Delete_management(self._tempGDBPath)
        arcpy.CreateFileGDB_management(self._outputDirectory, gdbName, "CURRENT")
        
    def splitAddressRanges (self):
        
        identityFeature = "testingIdentity"
        isStartField = "isStart"
        wholeLengthField = "wholeLength"
        errorField = "isError"
        errorNotesField = "errNotes"
                
        frequencyTable = "freqTable"
        frequencyIdField = self._getFrequencyFieldName()
        rangeAssigner = NewRangeAssignment.NewRangeAssignment(isStartField, wholeLengthField, frequencyIdField, errorField, errorNotesField)
        
        self._createTempGDB(self._tempGDBName)
        arcpy.env.workspace = self._tempGDBPath
        
        self._deleteIfExists(identityFeature)
        arcpy.Identity_analysis(self._wholeRoads, self._boundaries, identityFeature, "ONLY_FID")
        self._addFieldsToIdentityRds(identityFeature, isStartField, wholeLengthField, errorField, errorNotesField)
        
        print self._getFrequencyFieldName()
        arcpy.Frequency_analysis(identityFeature, frequencyTable, frequencyIdField)
        with arcpy.da.SearchCursor(frequencyTable, [frequencyIdField], """"FREQUENCY" >= 2""") as freqCursor:
            for row in freqCursor:
                print row[0]
                self._transferInfoFromWholeToIdentity(row[0], identityFeature, isStartField, wholeLengthField, errorField, errorNotesField)
                rangeAssigner.assignNewRange(identityFeature, row[0])
                print
        
        self._expandErrorFlagAcrossIdNumbers(identityFeature, errorField, errorNotesField, frequencyIdField)
        self._updateFeatures(identityFeature, frequencyIdField, wholeLengthField, errorField)       
        self._copyErrorFeatures(identityFeature, errorField, "Error_Roads")
        self._deleteTempLayers([identityFeature, frequencyTable])
        

             
                