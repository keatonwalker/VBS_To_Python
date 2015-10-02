'''
Created on Jul 30, 2013

@author: kwalker
'''
import AddressSplitterTool


if __name__ == "__main__":
    
    roads = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\AddressRangeTestData.gdb\roadTestSet"
    boundaries = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\AddressRangeTestData.gdb\polyBoundTestSet"
    outputDir = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\VBA_To_Python\AddressRangeSplitterTool\data\testOutputs"
    
    splitter = AddressSplitterTool.AddressRangeSplitter(roads, boundaries, outputDir)
    splitter.splitAddressRanges()