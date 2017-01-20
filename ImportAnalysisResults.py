# ---------------------------------------------------------------------------
# NAME: ImportAnalysisResults.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: ImportAnalysisResults <input_analysis_database> <input_analysis_table>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#   input_analysis_table - Name and location of table containing analysis results
#
# Description:  Import HEA results from analysis database results table and create output grid 
#              contaminant threshold table
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: September 20, 2010
# Date Modified: June 1, 2011       - Added symbology layer application
#                September 15, 2012 - Changed to utilize user supplied contaminant name, Additional bug fixes
#                March 11, 2014     - updated to arcpy for V2.0
# 
# ---------------------------------------------------------------------------

class noresults(Exception):
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

# Assign scratch workspace 
scratchWS = env.scratchWorkspace

try:
    # Report version...
    ver = ARD_HEA_Tools.version()
    arcpy.AddMessage("ARD HEA Tools Version: " + ver)

    # Script arguments...
    geoDB = sys.argv[1]
    resDB = sys.argv[2]
    scnDB = sys.argv[3]
    ischecked = sys.argv[4]

    # Local variables...
    inPts = geoDB + "\\ANALYSIS_PNTS"
    usrTbl = geoDB + "\\ANALYSIS_RESULTS"
    scnTbl = geoDB + "\\ANALYSIS_SCENARIOS"
    tmpDSAYTbl = geoDB + "\\DSAY_RESULTS"
    tmpInjTbl = geoDB + "\\PERCENT_INJURY_RESULTS"
    
    resTbl = resDB + "\\ANALYSIS_DSAY_By_Grid_Year"
    injTbl = resDB + "\\ANALYSIS_Perc_Injury_Summary_by_Grid"
    genTbl = scnDB + "\\USER_General_Inputs"

    AnalysisGrid = geoDB + "\\ANALYSIS_GRID"
    scriptPath = sys.path[0]
    xmlTemp = scriptPath + "\\result_dsays_metadata_template.xml"
    layerFile = scriptPath + "\\DSAY_5CL.lyr"

    if arcpy.Exists(resTbl) == False:
        raise noresults
    if str(ischecked) == 'true' and arcpy.Exists(injTbl) == False:
        raise nopctinjury
    
    desc = arcpy.Describe(AnalysisGrid)
    grdCellSize = desc.MeanCellHeight

    # Set the geoprocessing environment
    env.overwriteOutput = 1

    # Process: Import analysis results table...
    arcpy.AddMessage("Getting analysis scenarios...")
    if arcpy.Exists(scnTbl):
        arcpy.Delete_management(scnTbl)
    arcpy.TableToTable_conversion(genTbl, geoDB, "ANALYSIS_SCENARIOS")    

    # Process: Import analysis results table...
    arcpy.AddMessage("Getting analysis results...")
    if arcpy.Exists(usrTbl):
        arcpy.Delete_management(usrTbl)
    if str(ischecked) == 'true':
        arcpy.TableToTable_conversion(resTbl, geoDB, "DSAY_RESULTS")
        arcpy.TableToTable_conversion(injTbl, geoDB, "PERCENT_INJURY_RESULTS")
        arcpy.AddField_management(tmpDSAYTbl, "TMPJOIN", "TEXT")
        arcpy.CalculateField_management(tmpDSAYTbl, "TMPJOIN", "str(!Grid_ID!) + '_' + str(!ExpYear!)", "PYTHON")
        arcpy.AddField_management (tmpInjTbl, "TMPJOIN", "TEXT")
        arcpy.CalculateField_management(tmpInjTbl, "TMPJOIN", "str(!Grid_ID!) + '_' + str(!ExpYear!)", "PYTHON")
        arcpy.TableToTable_conversion(tmpDSAYTbl, geoDB, "ANALYSIS_RESULTS")
        arcpy.JoinField_management(usrTbl, "TMPJOIN", tmpInjTbl, "TMPJOIN", "PERCENT_INJURY")
        arcpy.DeleteField_management(usrTbl, "TMPJOIN")
        arcpy.Delete_management(tmpDSAYTbl)
        arcpy.Delete_management(tmpInjTbl)
    else:
	arcpy.TableToTable_conversion(resTbl, geoDB, "ANALYSIS_RESULTS")

    # Search results table for scenarios count and maximum year
    valueList = []
    maxyear = 0
    field = "Scenario_ID"
    rows = arcpy.SearchCursor(usrTbl)
    row = rows.next()
    while row:
        valueList.append(row.getValue(field))
        row = rows.next()
    uniqueSet = set(valueList)
    uniqueScen = list(uniqueSet)
    uniqueScen.sort()
    del rows
    del row
    arcpy.AddMessage("Scenarios with results: "+str(uniqueScen))
    env.qualifiedFieldNames = "UNQUALIFIED"

    # Make a point layer for each scenario by copying ANALYSIS_POINTS and cursoring through results table for each grid cell
    for scen in uniqueScen:
        scname = ARD_HEA_Tools.sanitizetext(str(scen))
        rows = arcpy.SearchCursor(scnTbl, "[Scenario_ID] = " + str(scen))
        row = rows.next()
        while row:
            if row.getValue("Scenario_Name") is not None or row.getValue("Scenario_Name") != " ":
                text = row.getValue("Scenario_Name")
                scname = ARD_HEA_Tools.sanitizetext(str.upper(str(text)))
            row = rows.next()
        del rows
        del row
        
        #Setup temp and output files
        outTbl = geoDB + "\\SC" + str(scen) + "_" + scname + "_RESULT_TBL"
        if arcpy.Exists(outTbl):
            arcpy.Delete_management(outTbl)
        outPts = geoDB + "\\SC" + str(scen) + "_" + scname + "_RESULT_PNTS"
        if arcpy.Exists(outPts):
            arcpy.Delete_management(outPts)               
        outDSAY = geoDB + "\\SC" + str(scen) + "_" + scname + "_DSAY"
	outPCT = geoDB + "\\SC" + str(scen) + "_" + scname + "_PCT_INJ"
        if arcpy.Exists(outDSAY):
            arcpy.Delete_management(outDSAY)

        #Make temp point layer with appropriate fields
        arcpy.AddMessage("Creating output for Scenario #:" + str(scen) + ", Name: " + scname )
        arcpy.MakeTableView_management(usrTbl, "tmpTbl", "[Scenario_Id] = "+ str(scen))
        if str(ischecked) == 'true':
            arcpy.Statistics_analysis("tmpTbl", outTbl, "DSAY_Injury SUM; SAY_Injury MAX; ExpYear MAX; PERCENT_INJURY MAX", "Grid_ID") 
        else:
            arcpy.Statistics_analysis("tmpTbl", outTbl, "DSAY_Injury SUM; SAY_Injury MAX; ExpYear MAX", "Grid_ID") 
        arcpy.MakeFeatureLayer_management(inPts, "SiteJoinView")
        arcpy.AddJoin_management("SiteJoinView", "GRID_ID", outTbl, "GRID_ID", "KEEP_ALL")
        arcpy.CopyFeatures_management("SiteJoinView", outPts)
        arcpy.AddField_management(outPts, "DSAY_INJ", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(outPts, "SAY_INJ", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        if str(ischecked) == 'true':
	    arcpy.AddField_management(outPts, "PCT_INJ", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(outPts, "MAX_YEAR", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        #Update DSAY values
        rows = arcpy.UpdateCursor(outPts)
        row = rows.next()
        while row:
            if row.sum_DSAY_Injury is not None:
                row.DSAY_INJ = row.SUM_DSAY_Injury
                row.SAY_INJ = row.MAX_SAY_Injury
                if str(ischecked) == 'true':
                    row.PCT_INJ = row.MAX_PERCENT_INJURY
                row.MAX_YEAR = row.MAX_ExpYear
            else:
                row.DSAY_INJ = 0
                row.SAY_INJ = 0
                if str(ischecked) == 'true':
                    row.PCT_INJ = 0
            rows.updateRow(row)
            row = rows.next()
        del row
        del rows
        arcpy.DeleteField_management(outPts, "GRID_ID_1; FREQUENCY; SUM_DSAY_Injury; MAX_SAY_Injury; MAX_ExpYear")
        if str(ischecked) == 'true':
            arcpy.DeleteField_management(outPts, "MAX_PERCENT_INJURY")
        arcpy.PointToRaster_conversion(outPts, "DSAY_INJ", outDSAY, "MAXIMUM", "", grdCellSize)
        if str(ischecked) == 'true':
            arcpy.PointToRaster_conversion(outPts, "PCT_INJ", outPCT, "MAXIMUM", "", grdCellSize)

        #Import metadata template...
	arcpy.AddMessage("importing metadata from " + xmlTemp + " to " + outDSAY)
        arcpy.ImportMetadata_conversion(xmlTemp, "FROM_FGDC", outDSAY, "ENABLED")
        # arcpy.MetadataImporter_conversion(xmlTemp, outDSAY)
        arcpy.Delete_management(outTbl)
        arcpy.Delete_management(outPts)

except noresults:
    arcpy.AddError("\n*** ERROR *** " + resTbl + ": Cannot find results table(s).  Make sure you have selected a valid HEA calculation database.\n")
    print "\n*** ERROR *** " + resTbl + ": Cannot find results table(s).  Make sure you have selected a valid HEA calculation database.\n"    

except nopctinjury:
    arcpy.AddError("\n*** ERROR *** " + resTbl + ": Cannot find the ANALYSIS_Perc_Injury_Summary_by_Grid table.\n")
    print "\n*** ERROR *** " + resTbl + ": Cannot find the ANALYSIS_Perc_Injury_Summary_by_Grid table.\n"

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


