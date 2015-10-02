'''
Created on Jul 31, 2013

@author: kwalker
'''
import arcpy

class NewRangeAssignment(object):
    
    _isStartField = ""
    _wholeLengthField = ""
    _frequencyIdField = ""
    _errorField = ""
    _errorNotesField = ""
    _leftFromField = ""
    _leftToField = ""
    _rightFromField = ""
    _rightToField = ""
    
    def __init__(self, isStartFieldName, wholeLengthFieldName, frequencyIdFieldName, errorFieldName, errorNotesFieldName):
        self._isStartField = isStartFieldName
        self._wholeLengthField = wholeLengthFieldName
        self._frequencyIdField = frequencyIdFieldName
        self._errorField = errorFieldName
        self._errorNotesField = errorNotesFieldName
        self._leftFromField = "L_F_ADD"
        self._leftToField = "L_T_ADD"
        self._rightFromField = "R_F_ADD"
        self._rightToField = "R_T_ADD"
        
    def _isStr_EmptyNULL(self, fieldString):
        return fieldString == "" or fieldString == None or fieldString == " "
    
    def _calculateNewRange(self, currentRange, lengthPercent):
        #currentRange = abs(fromValue - toValue)        
        newRange = round(currentRange * lengthPercent)
        
        return newRange

    def _caclulateNewEndValue(self, non_updatedFromOrToValue, newRange):
        currentEvenOddAdjusment = non_updatedFromOrToValue %  2
        
        newEndValue = non_updatedFromOrToValue + newRange
        newEndEvenOddAdjusment = abs((newEndValue % 2) - currentEvenOddAdjusment)
        newEndValue += newEndEvenOddAdjusment
     
        return newEndValue       
        
        
    def _getLengthPercentage(self, partLength, wholeLength):
        return partLength / wholeLength
        
    def assignNewRange(self, identityFeature, IdNumber):
        cursorFields = ["SHAPE@", self._isStartField, self._wholeLengthField,
                         self._leftFromField, self._leftToField, self._rightFromField, self._rightToField,
                         self._errorField, self._errorNotesField]
        sqlClause = (None, 'Order By {0} DESC'.format(self._isStartField))
        firstRoadLeftNewEndValue = 0
        firstRoadRightNewEndValue = 0

        with arcpy.da.UpdateCursor(identityFeature, cursorFields, """"{}" = {}""".format(self._frequencyIdField, IdNumber), sql_clause=sqlClause) as identityCursor:            
            for row in identityCursor:
                
                if row[3] == None or row[4] == None or row[5] == None or row[6] == None:
                    row[7] = 1
                    row[8] = "Not Updated: One or more addresses Null"
                    identityCursor.updateRow(row)
                    continue
                
                leftRange = abs(row[3] - row[4])
                leftNewRange = self._calculateNewRange(leftRange, self._getLengthPercentage(row[0].length, row[2]))
                rightRange = abs(row[5] - row[6])               
                rightNewRange = self._calculateNewRange(rightRange, self._getLengthPercentage(row[0].length, row[2]))
                print"{}: lNE: {} rNE: {}".format(IdNumber, leftNewRange, rightNewRange)
                
                if row[1] == 1:
                    
                    if row[3] < row[4]:
                        row[4] = self._caclulateNewEndValue(row[3], leftNewRange)
                        firstRoadLeftNewEndValue = row[4]     
                    else:
                        row[3] = self._caclulateNewEndValue(row[4], leftNewRange) 
                        firstRoadLeftNewEndValue = row[3]  
                    
                    if row[5] < row[6]:
                        row[6] = self._caclulateNewEndValue(row[5], rightNewRange) 
                        firstRoadRightNewEndValue = row[6]      
                    else:
                        row[5] = self._caclulateNewEndValue(row[5], rightNewRange)
                        firstRoadRightNewEndValue = row[5]   
                        
                else:
                    nonStartRoadAdjustValue = 2
                    if row[3] == 0 and row[4] == 0 and row[5] == 0 and row[6] == 0:
                        nonStartRoadAdjustValue = 0
                       
                    if row[3] < row[4]:
                        row[3] = firstRoadLeftNewEndValue + nonStartRoadAdjustValue    
                    else:
                        row[4] = firstRoadLeftNewEndValue + nonStartRoadAdjustValue 
                    
                    if row[5] < row[6]:
                        row[5] = firstRoadRightNewEndValue + nonStartRoadAdjustValue  
                    else:
                        row[6] = firstRoadRightNewEndValue + nonStartRoadAdjustValue   
                        
                identityCursor.updateRow(row)
                    
                        
                        