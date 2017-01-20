# ---------------------------------------------------------------------------
# NAME: LoadSiteAttributes.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: LoadSiteAttributes <input_analysis_database> <input_feature_layer> <input_habitat> 
#						   <input_condition> <input_remediation> <input_subsite> <input_depth> <site_attribute_documentation>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#   input_feature_layer - Name of feature layer to load into database
#	input_habitat - Habitat type field
#	input_condition - Condition type field
#	input_remediation - Remediation status field
#	input_subsite - Subsite division field
#	input_depth - Depth field
#   site_attribute_documentation - Name and location of the metadata text or xml file for the site attribute layer
#
# Description: Loads ancillary data into a single data table for further data
#              analysis.
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.  User
#         should be aware of overlapping polygons with differenct attributes.  The tool
#         will only load one attribute by design.
#
# Date Created: March 7, 2010
# Date Modified: March 16, 2010     - Added ability to update SITE_ATTRIBUTES data table allowing the tool to be run for multiple layers
#                October 27, 2010   - Changed code to replace Intersect and JoinField GP commands with SpatialJoin and AddJoin respectively to avoid use of ArcINFO license
#                November 16, 2010  - Added filters for all non-letter or digit characters except underscores
#                June 1, 2011       - Edited for Arc 10.0 functionality, added site attribute documentation tracking
#                September 15, 2012 - Additional bug fixes
#                March 11, 2014     - updated to arcpy for V2.0
#                March 6, 2015      - Added code to remove spaces from habitat feature layer name used as a base for temporary join feature class name
#                March 11, 2015     - added code to check if depth field in the SITE_ATTRIBUTES table is called "DEPTH" (legacy) or "DEPTH_ID"
#
# ---------------------------------------------------------------------------

class badvalues(Exception):
    pass

class nofeatures(Exception):
    pass

# Import system modules
import ARD_HEA_Tools
import sys
import string
import os
import traceback
import arcpy
from arcpy import env

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

# Load required toolboxes...
sub_folder = "ArcToolbox/Toolboxes/"
install_dir = arcpy.GetInstallInfo("desktop")['InstallDir'].replace("\\","/")
tbx_home = os.path.join(install_dir, sub_folder)
arcpy.AddToolbox(tbx_home+"Spatial Analyst Tools.tbx")
arcpy.AddToolbox(tbx_home+"Data Management Tools.tbx")
arcpy.AddToolbox(tbx_home+"Conversion Tools.tbx")

def updatecursorvalue (inputField, outputField, naValue):
    if row.getValue(inputField) is None or row.getValue(inputField) == " ":
        row.setValue(outputField, naValue)
    elif len(str(row.getValue(inputField))) > 0:
        text = str(row.getValue(inputField))
        row.setValue(outputField, ARD_HEA_Tools.sanitizetext(text))
    else:
        row.setValue(outputField, naValue)

def insertcursorvalue (inputField, outputField, naValue):
    if rowJoin.getValue(inputField) is None or rowJoin.getValue(inputField) == " ":
        rowSite.setValue(outputField, naValue)
    elif len(str(rowJoin.getValue(inputField))) > 0:
        text = str(rowJoin.getValue(inputField))
        rowSite.setValue(outputField, ARD_HEA_Tools.sanitizetext(text))
    else:
        rowSite.setValue(outputField, naValue)

def updateprojectdoc (inputText, outputField, projectTable):
    rowsProj = arcpy.UpdateCursor(projectTable)
    rowProj = rowsProj.next()
    if rowProj:
        if inputText is not None:
            rowProj.setValue(outputField, inputText)
        rowsProj.updateRow(rowProj)
    del rowsProj
    del rowProj


try:
    # Report version...
    ver = ARD_HEA_Tools.version()
    arcpy.AddMessage("ARD HEA Tools Version: " + ver)

    # Script arguments...
    geoDB = sys.argv[1]
    inLayer = sys.argv[2]
    habType = sys.argv[3]
    conType = sys.argv[4]
    remStat = sys.argv[5]
    subSite = sys.argv[6]
    siteDoc = sys.argv[7]
    depth = "-not applicable-"

    # Local variables...
    desc = arcpy.Describe(inLayer)
    if desc.dataType == "FeatureLayer":
        inBase = ARD_HEA_Tools.sanitize(inLayer.split(os.sep)[-1])
    else:
        inBase = desc.BaseName
    AnalysisGrid = geoDB + "\\ANALYSIS_GRID"
    AnalysisPnts = geoDB + "\\ANALYSIS_PNTS"

    inJoin = geoDB + "\\" + inBase + "_ident"
    inJoinLyr = inBase + "_ident_lyr"
    SiteAttr = geoDB + "\\SITE_ATTRIBUTES"
    tmpJoin = geoDB + "\\SITE_JOIN_VIEW"
    prjAttr = geoDB + "\\PROJECT_ATTRIBUTES"

    # Set the geoprocessing environment...
    env.overwriteOutput = 1
    env.XYTolerance = "0.00000000000000000001"

    #Read in site attribute document
    if arcpy.Exists(siteDoc):
        f = open(siteDoc, "r")
        readText = f.read()
        siteText = readText.decode('ascii', 'ignore')
        f.close()
    else:
        siteText = None    

    # Check for acceptable values...
    if conType <> "-not applicable-":
        arcpy.AddMessage("Checking for values...")
        valueList = []
        rows = arcpy.SearchCursor(inLayer)
        row = rows.next()
        while row:
            if row.getValue(conType) is not None and row.getValue(conType) not in ("FF", "BA", "D", "NA"):
                raise badvalues
            row = rows.next()
        del rows
        del row
    
    # Process: Check to see if polygons intersect with grid...
    arcpy.AddMessage("Intersecting with grid...")
    arcpy.MakeFeatureLayer_management(AnalysisPnts, "tmpLyr")
    arcpy.SelectLayerByLocation_management("tmpLyr", "INTERSECT", inLayer)
    result = arcpy.GetCount_management("tmpLyr")
    if int(result.getOutput(0)) == 0:
        raise nofeatures
    arcpy.Delete_management("tmpLyr")
    
    # Process: Spatial join with grid points
    arcpy.AddMessage("Joining...")
    arcpy.SpatialJoin_analysis(AnalysisPnts, inLayer, inJoin, "JOIN_ONE_TO_ONE", "KEEP_ALL")
    arcpy.AddMessage("finished join")
    
    # Determine what the depth field is called in the SITE_ATTRIBUTES table
    fieldList = arcpy.ListFields(SiteAttr)
    for fld in fieldList:
        if fld.name == "DEPTH_ID":
            DepthFld = "DEPTH_ID"
        elif fld.name == "DEPTH":
            DepthFld = "DEPTH"

    # Process: Update temporary attribute table...
    result = arcpy.GetCount_management(SiteAttr)
    env.qualifiedFieldNames = "UNQUALIFIED"

    # Update documentation..
    if habType <> "-not applicable-":
        updateprojectdoc(siteText, "SITE_HABITAT_DOC", prjAttr)
    if conType <> "-not applicable-":
        updateprojectdoc(siteText, "SITE_CONDITION_DOC", prjAttr)
    if remStat <> "-not applicable-":
        updateprojectdoc(siteText, "SITE_REMEDIATION_DOC", prjAttr)
    if subSite <> "-not applicable-":
        updateprojectdoc(siteText, "SITE_SUBSITE_DOC", prjAttr)
    if depth <> "-not applicable-":
        updateprojectdoc(siteText, "SITE_DEPTH_DOC", prjAttr)

    if int(result.getOutput(0)) > 0:
        arcpy.AddMessage("Adding records to database table...")
        arcpy.AddIndex_management(inJoin, "GRID_ID", "STAT_GRD_IDX", "UNIQUE", "ASCENDING")
        arcpy.MakeTableView_management(SiteAttr, "SiteJoinView")
        arcpy.AddJoin_management("SiteJoinView", "GRID_ID", inJoin, "GRID_ID", "KEEP_ALL")
        arcpy.CopyRows_management("SiteJoinView", tmpJoin)
        arcpy.AddIndex_management(tmpJoin, "GRID_ID", "GRD_IDX", "UNIQUE", "ASCENDING")

        # Get list of fields to delete later...
        fldList = None
        fldList = arcpy.ListFields(tmpJoin)
        flds = []
        for field in fldList:
            flds.append(str(field.name))
        last = len(flds)
        delList = str(flds[7:last]).strip("[]").replace(",",";").replace("'","").strip(None)

        # Update cursor
        rows = arcpy.UpdateCursor(tmpJoin)
        row = rows.next()
        while row:
            if habType <> "-not applicable-":
                updatecursorvalue(habType, "HABITAT_ID", "NA")
            if conType <> "-not applicable-":
                updatecursorvalue(conType, "CONDITION_ID", "NA")
            if remStat <> "-not applicable-":
                updatecursorvalue(remStat, "REMEDIATION_ID", "NA")
            if subSite <> "-not applicable-":
                updatecursorvalue(subSite, "SUBSITE_ID", "NA")
            if depth <> "-not applicable-":
                updatecursorvalue(depth, DepthFld, "-999.9")
            rows.updateRow(row)
            row = rows.next()
        del row
        del rows
        arcpy.DeleteField_management(tmpJoin, delList)
        arcpy.CopyRows_management(tmpJoin, SiteAttr)
        
    else:
        arcpy.AddMessage("Inserting records in database table...")
        rowsJoin = arcpy.SearchCursor(inJoin)
        rowJoin = rowsJoin.next()
        rowsSite = arcpy.InsertCursor(SiteAttr)
        rowSite = rowsSite.newRow()
        while rowJoin:
            rowSite.GRID_ID = rowJoin.GRID_ID
            if habType <> "-not applicable-":
                insertcursorvalue(habType, "HABITAT_ID", "NA")
            if conType <> "-not applicable-":
                insertcursorvalue(conType, "CONDITION_ID", "NA")              
            if remStat <> "-not applicable-":
                insertcursorvalue(remStat, "REMEDIATION_ID", "NA")            
            if subSite <> "-not applicable-":
                insertcursorvalue(subSite, "SUBSITE_ID", "NA")                  
            if depth <> "-not applicable-":
                insertcursorvalue(depth, DepthFld, "-999.9")  
            rowsSite.insertRow(rowSite)
            rowJoin = rowsJoin.next()
        del rowSite
        del rowsSite
        del rowJoin
        del rowsJoin

    if arcpy.Exists(tmpJoin):
        arcpy.Delete_management(tmpJoin)
    if arcpy.Exists(inJoin):
        arcpy.Delete_management(inJoin)
    
    # Process: Compact database
    arcpy.Compact_management(geoDB)

except badvalues:
    arcpy.AddError("\n*** ERROR *** " + inLayer + ": Incorrect condition values in input layer.\nAcceptable values include: FF, BA, D, or NA.\n")
    print "\n*** ERROR *** " + inLayer + ": Incorrect condition values in input layer.\nAcceptable values include: FF, BA, D, or NA.\n"
    
except nofeatures:
    arcpy.AddError("\n*** ERROR *** " + inLayer + ": No features intersect with analysis grid\n")
    print "\n*** ERROR *** " + inLayer + ": No features intersect with analysis grid\n"

except arcpy.ExecuteError:
    # Get the tool error messages
    msgs = arcpy.GetMessage(0)
    msgs += arcpy.GetMessages(2)

    # Return tool error messages for use with a script tool
    arcpy.AddError(msgs)

    # Print tool error messages for use in Python/PythonWin
    print msgs
    
except:
    # Get the traceback object
    #
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    #
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    # Return python error messages for use in script tool or Python Window
    #
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)

    # Print Python error messages for use in Python / Python Window
    #
    print pymsg + "\n"
    print msgs


