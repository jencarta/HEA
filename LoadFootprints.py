# ---------------------------------------------------------------------------
# NAME: LoadFootprints.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: LoadFootprints <input_analysis_database>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#
# Description: Load footprints into the contaminant surface table
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: July 15, 2014
#
# Date Modified: March 5, 2015     - Added code to load footprints into COC_DATA table
#
# ---------------------------------------------------------------------------

# Import system modules
import ARD_HEA_Tools
import sys
import string
import os
import traceback
import arcpy
from arcpy.sa import *
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

try:
    # Report version...
    ver = ARD_HEA_Tools.version()
    arcpy.AddMessage("ARD HEA Tools Version: " + ver)
    
    # Script arguments...
    geoDB = sys.argv[1]
    ScenID = sys.argv[2]

    # Local variables...
    usrTbl = geoDB + "\\USER_THRESHOLDS"
    COCTbl = geoDB + "\\COC_DATA"
    arcpy.AddMessage("table " + COCTbl)
    footprints = geoDB + "\\FOOTPRINTS"

    # Set the geoprocessing environment
    env.overwriteOutput = 1

    # Check to see if FOOTPRINTS table already exists, and if it doesn't, create it
    if arcpy.Exists(footprints) == False:
	arcpy.AddMessage("Creating the FOOTPRINTS table")
        arcpy.CreateTable_management(geoDB, "FOOTPRINTS", "", "")
        arcpy.AddField_management(footprints, "GRID_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
	arcpy.AddField_management(footprints, "SCENARIO_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(footprints, "COC_NAME", "TEXT", "", "", "20", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(footprints, "FOOTPRINT_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Loop through each record in subset of contaminant threshold table and load associated footprint
    expression = arcpy.AddFieldDelimiters(usrTbl, "Scenario_ID") + " = " + ScenID
    with arcpy.da.SearchCursor(usrTbl, ("Scenario_ID", "COC_NAME"), where_clause=expression) as cursor:
        for row in cursor:
            COCName = row[1]
            FPRaster = geoDB + "\\" + COCName + "_SC" + ScenID

	    # Check to see if the footprint for this scenario and contaminant have already been loaded
	    cocvals = [row[0] for row in arcpy.da.SearchCursor((footprints), ("COC_NAME"))]
	    uniq_coc = set(cocvals)
	    scvals = [row[0] for row in arcpy.da.SearchCursor((footprints), ("SCENARIO_ID"))]
	    uniq_scen = set(scvals)
	    if (COCName in uniq_coc) and (int(ScenID) in uniq_scen):
		    arcpy.AddMessage("Scenario " +  ScenID + " footprint for contaminant " + COCName + " has already been loaded into the table.")
		    continue
	    # Check to make sure the footprint exists
	    elif arcpy.Exists(FPRaster) == False:
		    arcpy.AddMessage("Footprint for contaminant " + COCName + " does not exist.")
		    continue
	    else:
		    arcpy.AddMessage("Loading scenario " + ScenID + " footprint for contaminant " + COCName)
	    
            COC_FP = geoDB + "\\" + COCName + "SC" + ScenID + "_footprint"
            arcpy.Copy_management(geoDB + "\\ANALYSIS_PNTS", COC_FP)
            ExtractMultiValuesToPoints(COC_FP, [[FPRaster, "FOOTPRINT_ID"]], "NONE")

            # Add footprints to COC_DATA table
            arcpy.AddMessage("Adding footprints to COC_DATA table")
            joinfields = ['GRID_ID', 'FOOTPRINT_ID']
            joindict = {}
            with arcpy.da.SearchCursor(COC_FP, joinfields) as rows:
                for arow in rows:
                    joinval = arow[0]
                    val1 = arow[1]
                    joindict[joinval]=val1
            del arow, rows
            targetflds = ['GRID_ID', 'FOOTPRINT_ID']
            expression2 = arcpy.AddFieldDelimiters(COCTbl, "COC_NAME") + " = '" + COCName + "'"
            with arcpy.da.UpdateCursor(COCTbl, targetflds, where_clause=expression2) as recs:
                for rec in recs:
                    keyval = rec[0]
                    rec[1] = joindict[keyval]
                    recs.updateRow(rec)
            del rec, recs
	    
	    arcpy.AddField_management(COC_FP, "SCENARIO_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
	    arcpy.CalculateField_management(COC_FP, "SCENARIO_ID", ScenID)
	    arcpy.AddField_management(COC_FP, "COC_NAME", "TEXT", "", "", "20", "", "NULLABLE", "NON_REQUIRED", "")
	    arcpy.CalculateField_management(COC_FP, "COC_NAME", '"' + COCName + '"')
                
        # Make a table view of the points and append to FOOTPRINTS table
        arcpy.MakeTableView_management(COC_FP, "fp_view") 
        arcpy.Append_management("fp_view", footprints, "NO_TEST")
        arcpy.Delete_management(COC_FP)

    del row, cursor
    

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

