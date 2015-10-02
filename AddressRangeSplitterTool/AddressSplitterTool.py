'''
Created on Aug 5, 2013

@author: kwalker
'''
import arcpy, os, math, traceback

'''
Created on Jul 2, 2013

@author: kwalker
'''
import arcpy
from arcpy.da import SearchCursor, UpdateCursor
from operator import itemgetter

class Y_handler():
    inputRoad = r'C:\KW_Working\RoadsDescriber\TestLayers.gdb\RD070026'
    _orderField = "OrderNumber"
    yForkField = "Y_Fork"
    _endRoadField  = "endRoad"
    
    def __init__(self, inputRoadPath, orderFieldName, yForkFieldName, endRoadFieldName):
        self.inputRoad = inputRoadPath
        self._orderField = orderFieldName
        self.yForkField = yForkFieldName
        self._endRoadField = endRoadFieldName
    
    def _recalcOrderNumberBeforeY(self, minOrderNum, maxOrderNum, ySubgroupValue):
        whereClause = """("{0}" <> '{1}' AND {2} >= {3}) OR ("{0}" IS NULL  AND {2} >= {3})""".format(self.yForkField, 
                                                                      ySubgroupValue, 
                                                                      self._orderField, 
                                                                      minOrderNum)
        incExpression = """!{0}! + {1}""".format(self._orderField, (maxOrderNum - minOrderNum) + 1)
        if arcpy.Exists("orderRecalc"):
            arcpy.Delete_management("orderRecalc")      
        arcpy.MakeFeatureLayer_management(self.inputRoad, "orderRecalc", whereClause)
        arcpy.CalculateField_management ("orderRecalc", self._orderField, incExpression, "PYTHON_9.3")
    
    def _reverseY_OrderNumbers(self,minOrderNum, maxOrderNum, ySubgroupValue):
        whereClause = """"{0}" = '{1}'""".format(self.yForkField, ySubgroupValue)
        minToMaxOrderNumber = range(minOrderNum, maxOrderNum + 1)
        sqlClause = (None, 'Order By {0} DESC'.format(self._orderField))
        i = 0
        with arcpy.da.UpdateCursor(self.inputRoad, [self._orderField], whereClause, sql_clause=sqlClause) as maxToMinOrderCursor:
            for row in maxToMinOrderCursor:
                print "{0} = {1}".format(row[0], minToMaxOrderNumber[i])
                row[0] = minToMaxOrderNumber[i]
                maxToMinOrderCursor.updateRow(row) 
                i += 1
        
    def _removeMainRoadY_Flags(self, startingMainRdRow, ySubgroupSelection):
        prevShape = startingMainRdRow[1]
        prevOrderNum = startingMainRdRow[0]
        sqlClause = (None, 'Order By {0} DESC'.format(self._orderField))
        
        with arcpy.da.UpdateCursor(ySubgroupSelection, [self._orderField, "SHAPE@", self.yForkField], sql_clause=sqlClause) as yRemovingCursor:
            for row in yRemovingCursor:
                print row[0]
                if row[0] == prevOrderNum - 1 and row[1].touches(prevShape):
                    print "touching {0}".format(row[0])
                    row[2] = ""
                    yRemovingCursor.updateRow(row)
                    prevShape = row[1]
                    prevOrderNum = row[0]
        
    def _getStartingY_Oid(self, minOrderNum):
        whereClause = """"{0}" = {1}""".format(self._orderField, minOrderNum)
        justPickAnEnd = None
        with arcpy.da.SearchCursor(self.inputRoad, [self._orderField, "OID@", self._endRoadField], whereClause) as oidCursor:
            for row in oidCursor:
                justPickAnEnd = row[1]
                if row[2] != 1:
                    print "Hellooooooo!"
                    return row[1]
        
        return justPickAnEnd
    
    def _removeStartingMainRdY_Flag(self, startingOid):
        inputDesc = arcpy.Describe(self.inputRoad)
        inputOidName = inputDesc.OIDFieldName
        
        if arcpy.Exists("firstY"):
            arcpy.Delete_management("firstY")      
        arcpy.MakeFeatureLayer_management(self.inputRoad, "firstY", """"{0}" = {1}""".format(inputOidName, startingOid))
        arcpy.CalculateField_management ("firstY", self.yForkField, "''", "PYTHON_9.3")
        
    def _createForkSubgroups(self):
        whereClause = """"{0}" = 'Y'""".format(self.yForkField)
        sqlClause = (None, 'Order By {0} DESC'.format(self._orderField))
        with arcpy.da.UpdateCursor(self.inputRoad, [self._orderField, self.yForkField], whereClause, sql_clause=sqlClause) as forkCursor:
            ySubgroup = 0
            prevOrderNumber = 0
            for row in forkCursor:
                if prevOrderNumber - row[0] > 1:
                    ySubgroup += 1
                    
                row[1] = "Y{0}".format(ySubgroup)
                prevOrderNumber = row[0]
                forkCursor.updateRow(row)   
                #print row[0]
      
    def isolateRealY (self, ySubgroupValue):
    
        ySubgroupSelect = "MinSelection"
        whereClause = """"{0}" = '{1}'""".format(self.yForkField, ySubgroupValue)#""""{0}" = (SELECT MIN("{0}") FROM {1})""".format(self.orderField, ySubgroupSelect)
        print whereClause
        
        if arcpy.Exists(ySubgroupSelect):
            arcpy.Delete_management(ySubgroupSelect)      
        arcpy.MakeFeatureLayer_management(self.inputRoad, ySubgroupSelect, whereClause)
        
        yCursor = arcpy.da.SearchCursor(ySubgroupSelect, [self._orderField, "SHAPE@", "OID@"])
        sortedCursor = sorted(yCursor, key=itemgetter(0))#used to get cursor into tuple form
        del yCursor
        
        maxOrderRow = max(sortedCursor, key=itemgetter(0))
        minOrderRow = min(sortedCursor, key=itemgetter(0))
        print "Length of maxRow {}".format(len(maxOrderRow))
        print maxOrderRow
        
        maxOrderNum = maxOrderRow[0]
        minOrderNum = minOrderRow[0]
        
        startingMainRd_Oid = self._getStartingY_Oid(maxOrderNum)
        print startingMainRd_Oid
        print "-"
        self._removeStartingMainRdY_Flag(startingMainRd_Oid)
        startingMainRdRow = filter(lambda x : x[2] == startingMainRd_Oid, sortedCursor)[0]
        print filter(lambda x : x[2] == startingMainRd_Oid, sortedCursor)[0]
        self._removeMainRoadY_Flags(startingMainRdRow, ySubgroupSelect)
        print "*******"
        
        return [minOrderNum, maxOrderNum]

                
    def reorderY_Roads(self):
        self._createForkSubgroups()         
        arcpy.env.workspace = "in_memory"  
        uniqueYSubgroups = "ySubFreqtable"
        if arcpy.Exists(uniqueYSubgroups):
            arcpy.Delete_management(uniqueYSubgroups) 
        arcpy.Frequency_analysis(self.inputRoad, uniqueYSubgroups, self.yForkField)
        
        with arcpy.da.SearchCursor(uniqueYSubgroups, self.yForkField) as uniqYCursor:
            for row in uniqYCursor:
                if row[0] == None or row[0] == "":
                    continue
                minAndMaxOrderNums = self.isolateRealY (row[0])
                self._recalcOrderNumberBeforeY(minAndMaxOrderNums[0], minAndMaxOrderNums[1], row[0])
               
        arcpy.Delete_management(uniqueYSubgroups) 


class BreakHandler ():
    _inputRoad = ""
    _orderField = ""
    _endRoadField  = ""
    _breakField = ""
    
    def __init__(self, inputRoadPath, orderFieldName, endRoadFieldName):
        self._inputRoad = inputRoadPath
        self._orderField = orderFieldName
        self._endRoadField = endRoadFieldName
        self._breakField = "BREAK"
        
    def _distanceFormula(self, x1 , y1, x2, y2):
        d = math.sqrt((math.pow((x2 - x1),2) + math.pow((y2 - y1),2)))
        return d
    def addBreakField(self):
        arcpy.AddField_management(self._inputRoad, self._breakField, "SHORT")
    
    def _calcOrderNumberToBreakRow(self,oidBeforeBreak, oidAfterBreak):
        inputDesc = arcpy.Describe(self._inputRoad)
        inputOidName = inputDesc.OIDFieldName
        beforeBreakOrderNum = 0
        afterBreakRow = ""
        with arcpy.da.SearchCursor(self._inputRoad, 
                                   ["SHAPE@", self._orderField, "OID@"], 
                                   """"{0}" = {1}""".format(inputOidName, oidBeforeBreak)) as beforeBreakCursor:
            for row in beforeBreakCursor:    
                    beforeBreakOrderNum = row[1]
        
        with arcpy.da.UpdateCursor(self._inputRoad, 
                                   ["SHAPE@", self._orderField, "OID@", self._breakField], 
                                   """"{0}" = {1}""".format(inputOidName, oidAfterBreak)) as afterBreakCursor:
            for row in afterBreakCursor:    
                    row[1] = beforeBreakOrderNum + 1
                    row[3] = 1
                    afterBreakCursor.updateRow(row) 
                    afterBreakRow = row
        
        return afterBreakRow  
                    
    def getRoadRowAfterBreak(self, prevRoadRow):
        whereClause = """"{0}" = {1} AND "{2}" = 1""".format(self._orderField, 0, self._endRoadField)
        minDistance = -1
        minDistRow = ()
        
        print minDistance
        print whereClause
        with arcpy.da.SearchCursor(self._inputRoad, ["SHAPE@", self._orderField, "OID@"], whereClause) as breakConnectCursor:
            for row in breakConnectCursor:
                #print "LOOP"
                distanceToLastPoint = self._distanceFormula(row[0].firstPoint.X, row[0].firstPoint.Y, prevRoadRow[0].trueCentroid.X, prevRoadRow[0].trueCentroid.Y)
                distanceToFirstPoint = self._distanceFormula(row[0].lastPoint.X, row[0].lastPoint.Y, prevRoadRow[0].trueCentroid.X, prevRoadRow[0].trueCentroid.Y)
                
                if minDistance == -1:
                    minDistance = distanceToLastPoint
                    minDistRow = row
                    #print minDistRow[2]
                    
                if distanceToLastPoint < minDistance:
                    minDistance = distanceToLastPoint
                    minDistRow = row
                
                if distanceToFirstPoint < minDistance:
                    minDistance = distanceToFirstPoint
                    minDistRow = row
        
                    
        return self._calcOrderNumberToBreakRow(prevRoadRow[2], minDistRow[2])

class StartRoadFeature(object):

    
    _processedOIDs = []
    _endRds = []
    _inputRoad = ""
    _endRoadField = ""
    
    def __init__(self,  inputRoadPath, endRoadFieldName):
        self._inputRoad = inputRoadPath
        self._endRoadField = endRoadFieldName
        self._endRds = []
        self._processedOIDs = []
        
    def _addEndRoadField(self):
        arcpy.AddField_management(self._inputRoad, self._endRoadField, "SHORT")
    
    def _getTrend_Direction (self, extent):
        if extent.height > extent.width:
            return 'SN'
        else:
            return 'WE'
        
    def _findEndRoads(self, searchRoadRow):
        numOfConnections = 0
        with arcpy.da.SearchCursor(self._inputRoad, ["SHAPE@", "OID@"]) as connectionCursor:
            for row in connectionCursor:
                #print row[1]
                if searchRoadRow[0].touches(row[0]):
                    #print "sfdf"
                    numOfConnections += 1
                
        if numOfConnections <= 1:
            self._endRds.append(searchRoadRow)
            return True
        else:
            return False
              
    def _getOidClosestToBorderLine (self, extentCoordinate, trendDirection):
        closestOid = self._endRds[0][1]
        leastDistance = -1
        rdCoordinate = ""
    
        for rdRow in self._endRds:
            print "######### endRd OID: {0}".format(rdRow[1])
            if trendDirection == 'SN':
                rdCoordinate = rdRow[0].trueCentroid.Y
            elif trendDirection == 'WE':
                rdCoordinate = rdRow[0].trueCentroid.X
                
            rdRowDistance = rdCoordinate - extentCoordinate
            
            if leastDistance == -1:
                leastDistance = rdRowDistance
                closestOid = rdRow[1]
            elif rdRowDistance < leastDistance:
                leastDistance = rdRowDistance
                closestOid = rdRow[1]
        
        return closestOid
        

    def getStartFeatureOid(self, originalRoad):    
        rdDesc = arcpy.Describe(self._inputRoad)
        rdExtent = rdDesc.extent
        extentCoordinate = 0
        trendDirection = self._getTrend_Direction(rdExtent)
        self._addEndRoadField()

        closestId = ""
        with arcpy.da.UpdateCursor(self._inputRoad, ["SHAPE@", "OID@", self._endRoadField]) as rdCursor:
            for row in rdCursor:
                
                if originalRoad.firstPoint.touches(row[0]):
                    row[2] = 1
                    closestId = row[1]
                    rdCursor.updateRow(row)
                    break
                        
        print "First Feature OID: {0}".format(closestId)
        #print closestId
        return closestId
    
class EndPointFlipper():
    
    
    
    flipFlagField = "FLIPPER"
    _inputRoad = ""
    _orderField = ""
    
    def __init__(self,  inputRoadPath, orderFieldName):
        self._inputRoad = inputRoadPath
        self._orderField = orderFieldName
    
    def _needsAFlip(self, rdShape, orderNumber):
        needsAFlip = True
        with arcpy.da.SearchCursor(self._inputRoad, ["SHAPE@", self._orderField]) as Cursor:
            for row in Cursor:
                if int(row[1]) == orderNumber + 1 and row[0].touches(rdShape.lastPoint):
                    needsAFlip = False
                elif int(row[1]) == orderNumber - 1 and row[0].touches(rdShape.firstPoint):
                    needsAFlip = False

        return needsAFlip
    
    def _findRoutesToFlip(self):
        
        arcpy.AddField_management (self._inputRoad, self.flipFlagField, "SHORT")
        with arcpy.da.UpdateCursor(self._inputRoad, ["SHAPE@", self._orderField, self.flipFlagField, "OID@"]) as rdCursor:
            
            for row in rdCursor:
              
                if self._needsAFlip(row[0], row[1]):
                    #print"flippingit"
                    row[2] = 1
                    rdCursor.updateRow (row)

        if arcpy.Exists("flipSelection"):
            arcpy.Delete_management("flipSelection")                    
        arcpy.MakeFeatureLayer_management(self._inputRoad, "flipSelection", """"{0}" = 1""".format(self.flipFlagField))       
        arcpy.FlipLine_edit("flipSelection")


class RoadOrderingKw(object):
    _inputRoad = ""
    _orderField = ""
    _endRoadField = ""
    _yForkField = ""
    def __init__(self,  inputRoadPath, orderFieldName):
        self._inputRoad = inputRoadPath
        self._orderField = orderFieldName
        self._endRoadField = "endRoad"
        self._yForkField = "Y_Fork"
        
        self._originalRoad = ""
        
    def setOriginalRoad(self, originalRoad):
        self._originalRoad = originalRoad
        
    def _getFirstFeature(self):
        inputDesc = arcpy.Describe(self._inputRoad)
        inputOidName = inputDesc.OIDFieldName
        startRoad = StartRoadFeature(self._inputRoad, self._endRoadField)
        startingOid = startRoad.getStartFeatureOid(self._originalRoad)
        
        if arcpy.Exists("thefeature"):
            arcpy.Delete_management("thefeature")      
        firstFeatureLayer = arcpy.MakeFeatureLayer_management(self._inputRoad, "thefeature", """"{0}" = {1}""".format(inputOidName, startingOid))
        if int(arcpy.GetCount_management("thefeature").getOutput(0)) == 0:
            raise Exception("No first feature created for OID {0}".format(startingOid))
        else:
            return firstFeatureLayer
        
    def _isTrend_S_to_N (self, extent):
        if extent.height > extent.width:
            return True
        else:
            return False
    def _getNextConnectedRoads(self, prevSelectedRows):
        nextConnectedRoads = []
        whereClause = """"{0}" = {1}""".format(self._orderField, 0)
        
        with arcpy.da.UpdateCursor(self._inputRoad, ["SHAPE@", self._orderField, "OID@"], whereClause) as connectionCursor:
            for row in connectionCursor:
                for prevRow in prevSelectedRows:
                    if row[0].touches(prevRow[0]):
                        #print prevRow[1] + 1
                        row[1] = prevRow[1] + 1
                        if nextConnectedRoads.count(row) == 0:#protects agianst two previous features selecting the same next feature twice
                            nextConnectedRoads.append(row)
                        connectionCursor.updateRow(row)
        
        return nextConnectedRoads
        
    def _calcYforkfield(self):
        """Creates the Y_fork field and calculates it to Y for roads that have duplicate order numbers
         because the previous road selected 2 or more next roads"""
         
        yforkField = self._yForkField
        whereClause = """"FREQUENCY" >= 2"""
        arcpy.AddField_management (self._inputRoad, yforkField, "text", "", "", 10)
        arcpy.env.workspace = "in_memory"  
        orderNumberFreqTable = "orderNumberFrequency"
        if arcpy.Exists(orderNumberFreqTable):
                arcpy.Delete_management(orderNumberFreqTable) 
        arcpy.Frequency_analysis(self._inputRoad, orderNumberFreqTable, self._orderField)
        
        with arcpy.da.SearchCursor(orderNumberFreqTable, ["FREQUENCY", self._orderField], whereClause) as freqCursor:
            for row in freqCursor:
                if arcpy.Exists("YforkSelection"):
                    arcpy.Delete_management("YforkSelection") 
                arcpy.MakeFeatureLayer_management(self._inputRoad, "YforkSelection", """"{0}" = {1}""".format(self._orderField, row[1]))
                arcpy.CalculateField_management ("YforkSelection", yforkField, "'Y'", "PYTHON_9.3")
                
    
    def calculateOrderField (self):
        """Creates a field where the order of the road is recorded. The order field is populated with integers that 
        decrease from the starting segment untill the last segment. Y-fork splits and gaps will also be handled."""
        #stopWatch = ScriptRunTime.ScriptRunTime()
        print "*Ordering Road Feature: {}".format(self._inputRoad[-14:])
        breakHandler = BreakHandler(self._inputRoad, self._orderField, self._endRoadField)
        breakHandler.addBreakField()
        firstFeature =  self._getFirstFeature()
        #print "time after _getFirstFeature(): {0}".format(stopWatch.elapsedTime("min"))
        #add _orderField
        arcpy.AddField_management (self._inputRoad, self._orderField, "SHORT")
        if arcpy.Exists("calcOrderNumber"):
            arcpy.Delete_management("calcOrderNumber")         
        arcpy.MakeFeatureLayer_management(self._inputRoad, "calcOrderNumber")
        rdFeatureTotalCnt = int(arcpy.GetCount_management("calcOrderNumber").getOutput(0))
        arcpy.CalculateField_management ("calcOrderNumber", self._orderField, 0, "PYTHON_9.3")
         
        previousSelection = firstFeature
        
        orderNumI = 1
        arcpy.CalculateField_management (previousSelection, self._orderField, orderNumI, "PYTHON_9.3")###   
        processedRdCnt = 1
        prevSelectedRows = []
        with arcpy.da.SearchCursor(previousSelection, ["SHAPE@", self._orderField, "OID@"]) as firstRoadCursor:
            for row in firstRoadCursor:
                prevSelectedRows.append(row)
                
        while processedRdCnt < rdFeatureTotalCnt:
                       
            tempSelectedRows = self._getNextConnectedRoads(prevSelectedRows)
            if len(tempSelectedRows) == 0:#run road break function
                tempSelectedRows.append(breakHandler.getRoadRowAfterBreak(prevSelectedRows[0]))
                print "ASSDFSDF##############"
                #raise Exception("break error")
            processedRdCnt += len(tempSelectedRows)
            prevSelectedRows = tempSelectedRows
            if processedRdCnt % 50 == 0:
                print "Processed Count: {0}".format(processedRdCnt)
                
        #print "time after orderCalc: {0}".format(stopWatch.elapsedTime("min"))
        
        self._calcYforkfield()
        #print "time after _calcYforkfield(): {0}".format(stopWatch.elapsedTime("min"))
        
        endFlipper = EndPointFlipper(self._inputRoad, self._orderField)
        endFlipper._findRoutesToFlip()
        #print "time after _findRoutesToFlip(): {0}".format(stopWatch.elapsedTime("min"))
        yOrdering = Y_handler(self._inputRoad, self._orderField, self._yForkField, self._endRoadField)
        yOrdering.reorderY_Roads()    
        



class NewRangeAssignment(object):
    
    _orderField = ""
    _wholeLengthField = ""
    _frequencyIdField = ""
    _errorField = ""
    _errorNotesField = ""
    leftFromField = ""
    leftToField = ""
    rightFromField = ""
    rightToField = ""
    
    def __init__(self, orderFieldName, wholeLengthFieldName, frequencyIdFieldName, errorFieldName, errorNotesFieldName):
        self._orderField = orderFieldName
        self._wholeLengthField = wholeLengthFieldName
        self._frequencyIdField = frequencyIdFieldName
        self._errorField = errorFieldName
        self._errorNotesField = errorNotesFieldName
        self._yForkField = "Y_Fork"
        self.leftFromField = "L_F_ADD"
        self.leftToField = "L_T_ADD"
        self.rightFromField = "R_F_ADD"
        self.rightToField = "R_T_ADD"
        
    def _isStr_EmptyNULL(self, fieldString):
        return fieldString == "" or fieldString == None or fieldString == " "
    
    def _calculateNewRange(self, currentRange, lengthPercent):
        #currentRange = abs(fromValue - toValue)        
        newRange = round(currentRange * lengthPercent)
        
        return newRange

    def _caclulateNewEndValue(self, non_updatedFromOrToValue, newRange, maxOfRange):
        currentEvenOddAdjusment = non_updatedFromOrToValue %  2
        
        newEndValue = non_updatedFromOrToValue + newRange
        newEndEvenOddAdjusment = abs((newEndValue % 2) - currentEvenOddAdjusment)
        newEndValue += newEndEvenOddAdjusment
        
        if newEndValue >= maxOfRange:
            newEndValue -= 4
        
        if newEndValue < 0:
            newEndValue = 0
     
        return newEndValue       
        
        
    def _getLengthPercentage(self, partLength, wholeLength):
        return partLength / wholeLength

    def assignNewRange(self, identityFeature, IdNumber):
        
        maxLeft = 0
        maxRight  = 0
        lastSegment = 0
        searchFields = [self._orderField, self.leftFromField,
                 self.leftToField, self.rightFromField, self.rightToField,
                 self._errorField, self._errorNotesField, self._yForkField]
        sqlClause = (None, 'Order By {0} DESC'.format(self._orderField))
        with arcpy.da.SearchCursor(identityFeature, searchFields, """"{}" = {}""".format(self._frequencyIdField, IdNumber), sql_clause=sqlClause) as cursor:            
            for row in cursor:        
                maxLeft = max(row[1], row[2])
                maxRight = max(row[3], row[4])
                lastSegment = row[0]
                break
        
        cursorFields = ["SHAPE@", self._orderField, self._wholeLengthField,
                         self.leftFromField, self.leftToField, self.rightFromField, self.rightToField,
                         self._errorField, self._errorNotesField, self._yForkField]
        sqlClause = (None, 'Order By {0}'.format(self._orderField))
        firstRoadLeftNewEndValue = 0
        firstRoadRightNewEndValue = 0

        with arcpy.da.UpdateCursor(identityFeature, cursorFields, """"{}" = {}""".format(self._frequencyIdField, IdNumber), sql_clause=sqlClause) as identityCursor:            
            for row in identityCursor:
                print "\t" + str(IdNumber)
                if row[3] == None or row[4] == None or row[5] == None or row[6] == None:
                    row[7] = 1
                    row[8] = "One or more addresses Null"
                    identityCursor.updateRow(row)
                    continue
                if  row[9] != None:
                    row[7] = 1
                    row[8] = "Y fork road"
                    identityCursor.updateRow(row)
                    continue                   

                
                leftRange = abs(row[3] - row[4])
                leftNewRange = self._calculateNewRange(leftRange, self._getLengthPercentage(row[0].length, row[2]))
                print leftNewRange
                rightRange = abs(row[5] - row[6])               
                rightNewRange = self._calculateNewRange(rightRange, self._getLengthPercentage(row[0].length, row[2]))                
                #print"{}: lNE: {} rNE: {}".format(IdNumber, leftNewRange, rightNewRange)
                
                #Check for Y roads and flag any with isError field
                if row[3] == 0 and row[4] == 0 and row[5] == 0 and row[6] == 0:
                    continue #No need to update ranges if all are zero but geometery will still update
                
                elif row[1] == 1:
                    
                    if row[3] < row[4]:
                        row[4] = self._caclulateNewEndValue(row[3], leftNewRange, maxLeft)
                        firstRoadLeftNewEndValue = row[4]     
                    else:
                        row[3] = self._caclulateNewEndValue(row[4], leftNewRange, maxLeft) 
                        firstRoadLeftNewEndValue = row[3]  
                    
                    if row[5] < row[6]:
                        row[6] = self._caclulateNewEndValue(row[5], rightNewRange, maxRight) 
                        firstRoadRightNewEndValue = row[6]      
                    else:
                        row[5] = self._caclulateNewEndValue(row[5], rightNewRange, maxRight)
                        firstRoadRightNewEndValue = row[5]
                        
                elif row[1] == lastSegment:                  
                    
                    adjustValue = 2
                    if row[3] == 0 and row[4] == 0 and row[5] == 0 and row[6] == 0:
                        adjustValue = 0                    
                    
                    if row[3] < row[4]:
                        row[3] = firstRoadLeftNewEndValue + adjustValue
                        if row[3] >= maxLeft:
                            row[7] = 1
                            row[8] = "Segment too short to divide address range."
                        row[4] = maxLeft
                        print firstRoadLeftNewEndValue     
                    else:
                        row[4] = firstRoadLeftNewEndValue  + adjustValue
                        if row[4] >= maxLeft:
                            row[7] = 1
                            row[8] = "Segment too short to divide address range."
                        row[3] = maxLeft
                        print firstRoadLeftNewEndValue     
                    
                    if row[5] < row[6]:
                        row[5] = firstRoadRightNewEndValue  + adjustValue
                        if row[5] >= maxLeft:
                            row[7] = 1
                            row[8] = "Segment too short to divide address range."                        
                        row[6] = maxRight
                        print firstRoadRightNewEndValue      
                    else:
                        row[6] = firstRoadRightNewEndValue  + adjustValue
                        if row[6] >= maxLeft:
                            row[7] = 1
                            row[8] = "Segment too short to divide address range."                    
                        row[5] = maxRight
                        print firstRoadRightNewEndValue  
                        
                else:# Middle segements
                    
                    adjustValue = 2
                    if row[3] == 0 and row[4] == 0 and row[5] == 0 and row[6] == 0:
                        adjustValue = 0                    
                    
                    if row[3] < row[4]:
                        row[3] = firstRoadLeftNewEndValue + adjustValue
                        row[4] = self._caclulateNewEndValue(firstRoadLeftNewEndValue, leftNewRange, maxLeft)                       
                        firstRoadLeftNewEndValue = row[4]
                        print firstRoadLeftNewEndValue     
                    else:
                        row[4] = firstRoadLeftNewEndValue + adjustValue
                        row[3] = self._caclulateNewEndValue(firstRoadLeftNewEndValue, leftNewRange, maxLeft)
                        firstRoadLeftNewEndValue = row[3]
                        print firstRoadLeftNewEndValue     
                    
                    if row[5] < row[6]:
                        row[5] = firstRoadRightNewEndValue + adjustValue
                        row[6] = self._caclulateNewEndValue(firstRoadRightNewEndValue, rightNewRange, maxRight) 
                        firstRoadRightNewEndValue = row[6]
                        print firstRoadRightNewEndValue      
                    else:
                        row[6] = firstRoadRightNewEndValue + adjustValue
                        row[5] = self._caclulateNewEndValue(firstRoadRightNewEndValue, rightNewRange, maxRight)
                        firstRoadRightNewEndValue = row[5]
                        print firstRoadRightNewEndValue  
                        
                        
                identityCursor.updateRow(row)


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
        
    def _cleanIdentityOfMutlipartAndOverlaps(self, dirtyIdentityFeature):
        """Remove Multipart and overlapping feature from the identity results."""
        cleanedIdentityFeature = "cleanedIdentity"
        self._deleteIfExists(cleanedIdentityFeature)
        arcpy.DeleteIdentical_management(dirtyIdentityFeature, "Shape")
        arcpy.MultipartToSinglepart_management(dirtyIdentityFeature, cleanedIdentityFeature)
        
        return cleanedIdentityFeature
        
    
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

                       
                        identityRow[2] = wholeRow[0].length
                        identityCursor.updateRow(identityRow)
    
    def _createTempGDB(self, gdbName):
        if arcpy.Exists(self._tempGDBPath):
            arcpy.Delete_management(self._tempGDBPath)
        arcpy.CreateFileGDB_management(self._outputDirectory, gdbName, "CURRENT")
    
    def _orderIdentityFeatures(self, frequencyTable, frequencyIdField, identityFeature, orderField, lF, lT, rF, rT):
        with arcpy.da.SearchCursor(frequencyTable, [frequencyIdField], """"FREQUENCY" > 1""") as freqCursor:#May need to deal with "FREQUENCY" > 2 at some point
            for row in freqCursor:
                #order features
                wholeRoadShape = ""
                skipOrdering = False
                with arcpy.da.SearchCursor(self._wholeRoads, ["SHAPE@", lF, lT, rF, rT], """"{}" = {}""".format(self._getInputRoadOidName(), row[0])) as wholeRdCursor:
                    for wholeRow in wholeRdCursor:
                        if (wholeRow[1] == 0 and wholeRow[2] == 0 and wholeRow[3] == 0 and wholeRow[4] == 0) or \
                        (wholeRow[1] == None and wholeRow[2] == None or wholeRow[3] == None or wholeRow[4] == None):
                            skipOrdering = True
                        wholeRoadShape = wholeRow[0]
                        break
                    
                if skipOrdering:
                    print
                    print"_____________________Odering Skipped___________________________"
                    print row[0]


                

                else:
                    self._deleteIfExists("identityOrder")
                    print
                    print "order: " + str(row[0])
                    arcpy.MakeFeatureLayer_management(identityFeature, "identityOrder", """"{}" = {}""".format(frequencyIdField, row[0]))
                    roadOrder = RoadOrderingKw("identityOrder", orderField)                    
                    roadOrder.setOriginalRoad(wholeRoadShape)
                    try:
                        roadOrder.calculateOrderField()
                    except Exception as e:
                        print e
                        print "----------"
                        #traceback.print_exc()
                        arcpy.CalculateField_management ("identityOrder", "isError", 1)#change error field to param
                        arcpy.CalculateField_management ("identityOrder", "errNotes", '"Ordering failed"')
                        arcpy.CalculateField_management ("identityOrder", orderField, 0)
                    
                arcpy.env.workspace = self._tempGDBPath
                        
    def splitAddressRanges (self):
        
        dirtyIdentityFeature = "dirtyIdentity"
        identityFeature = ""
        orderField = "geoOrder"
        wholeLengthField = "wholeLength"
        errorField = "isError"
        errorNotesField = "errNotes"
                
        frequencyTable = "freqTable"
        frequencyIdField = self._getFrequencyFieldName()
        rangeAssigner = NewRangeAssignment(orderField, wholeLengthField, frequencyIdField, errorField, errorNotesField)
        
        self._createTempGDB(self._tempGDBName)
        arcpy.env.workspace = self._tempGDBPath
        
        #self._deleteIfExists(identityFeature)
        arcpy.AddMessage("Splitting roads on boundaries")
        arcpy.Identity_analysis(self._wholeRoads, self._boundaries, dirtyIdentityFeature, "ONLY_FID")
        identityFeature = self._cleanIdentityOfMutlipartAndOverlaps(dirtyIdentityFeature)
        self._addFieldsToIdentityRds(identityFeature, orderField, wholeLengthField, errorField, errorNotesField)
        
        print self._getFrequencyFieldName()
        arcpy.Frequency_analysis(identityFeature, frequencyTable, frequencyIdField)
        arcpy.AddMessage("Frequency of identity split roads created")
         
        self._orderIdentityFeatures(frequencyTable, frequencyIdField, identityFeature, orderField, rangeAssigner.leftFromField, rangeAssigner.leftToField,
                                                                                                     rangeAssigner.rightFromField, rangeAssigner.rightToField)
                       
        with arcpy.da.SearchCursor(frequencyTable, [frequencyIdField], """"FREQUENCY" > 1""") as freqCursor:
            for row in freqCursor:
                
                
                self._transferInfoFromWholeToIdentity(row[0], identityFeature, orderField, wholeLengthField, errorField, errorNotesField)
                rangeAssigner.assignNewRange(identityFeature, row[0])
                #print
        
        self._expandErrorFlagAcrossIdNumbers(identityFeature, errorField, errorNotesField, frequencyIdField)
        arcpy.AddMessage("Updating original road features")
        self._updateFeatures(identityFeature, frequencyIdField, wholeLengthField, errorField)
        arcpy.AddMessage("Creating error feature class")       
        self._copyErrorFeatures(identityFeature, errorField, "Error_Roads")
        arcpy.SetParameter(3, "Error_Roads")        
        self._deleteTempLayers([dirtyIdentityFeature, identityFeature, frequencyTable])
        
        

if __name__ == "__main__":
    

    roads = arcpy.GetParameterAsText(0)
    outputDir = arcpy.GetParameterAsText(2)
    boundaries = arcpy.GetParameterAsText(1)
     
    
    splitter = AddressRangeSplitter(roads, boundaries, outputDir)
    splitter.splitAddressRanges()  