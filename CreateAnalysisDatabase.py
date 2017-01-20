# ---------------------------------------------------------------------------
# NAME: CreateAnalysisDatabase.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: CreateAnalysisDatabase <output_database_location> <output_analysis_database> <analyst_name>
#
# Required Arguments: 
#   output_database_location - Name and location of folder to store analysis database
#   output_analysis_database - Name of analysis geodatabase
#   analyst_name - Name of analyst creating analysis geodatabase
#
# Description: Create and setup tables of the HEA geodatabase  
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: February 3, 2010
# Date Modified: February 15, 2010  - Added indexes to key fields on data tables
#                March 8, 2010      - Consolidated ANALYSIS_TABLE and COC_INVENTORY tables
#                                   - Added PROJECT_ATTRIBUTES table to track project related info
#                March 11, 2010     - Added UNITS field to PROJECT_ATTRIBUTES table
#                March 16, 2010     - Removed HABITAT_FUNCTION_ID from SITE_ATTRIBUTES table
#                June 1, 2011       - Edited for Arc 10.0 functionality, and changed data structure to store site attr. docs and analyst name
#                September 15, 2012 - Changed to create project folder and geoDB within, Additional bug fixes
#                September 17, 2013 - Converted to arcpy
#                July 21, 2014      - Added a FOOTPRINTS table for contaminant slices
#                March 4, 2015      - Added FOOTPRINT_ID field back into COC_DATA table
#                March 6, 2015      - Changed some fields to REQUIRED and NON_NULLABLE
#
# ---------------------------------------------------------------------------

# Import system modules
import ARD_HEA_Tools
import sys
import string
import os
import traceback
import arcpy

# Load required toolboxes...
sub_folder = "ArcToolbox/Toolboxes/"
install_dir = arcpy.GetInstallInfo("desktop")['InstallDir'].replace("\\","/")
tbx_home = os.path.join(install_dir, sub_folder)
arcpy.AddToolbox(tbx_home+"Data Management Tools.tbx")

try:
    # Report version...
    ver = ARD_HEA_Tools.version()
    arcpy.AddMessage("ARD HEA Tools Version: " + ver)

    # Script arguments...
    projDir = sys.argv[1]
    projNameIn = sys.argv[2]
    analystName = sys.argv[3]
    projName = ARD_HEA_Tools.sanitize(projNameIn)

    # Local variables...
    geoDBname = projName + "_GIS.mdb"
    geoDBfolder = projDir + "\\" + projName
    geoDB = geoDBfolder + "\\" + geoDBname
    prjAttr = geoDB + "\\PROJECT_ATTRIBUTES"
    COCData = geoDB + "\\COC_DATA"
    COCInvent = geoDB + "\\COC_INVENTORY"
    SiteAttr = geoDB + "\\SITE_ATTRIBUTES"
    COCAnalysis = geoDB + "\\ANALYSIS_TABLE"
    Footprint = geoDB + "\\FOOTPRINTS"

    # Create analysis folder
    arcpy.CreateFolder_management(projDir, projName)

    # Create analysis database
    arcpy.CreatePersonalGDB_management(geoDBfolder, geoDBname)

    # Create project data table
    arcpy.CreateTable_management(geoDB, "PROJECT_ATTRIBUTES", "", "")

    # Add fields to contaminant data table...
    arcpy.AddField_management(prjAttr, "CELL_SIZE", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "TOTAL_CELLS", "LONG", "", "", "", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(prjAttr, "UNITS", "TEXT", "", "", "10", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "ANALYST", "TEXT", "", "", "50", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "SITE_HABITAT_DOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "SITE_CONDITION_DOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "SITE_REMEDIATION_DOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "SITE_SUBSITE_DOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(prjAttr, "SITE_DEPTH_DOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")

    # Create contaminant data table
    arcpy.CreateTable_management(geoDB, "COC_DATA", "", "")

    # Add fields and indexes to contaminant data table...
    arcpy.AddField_management(COCData, "GRID_ID", "LONG", "", "", "", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCData, "COC_NAME", "TEXT", "", "", "20", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCData, "COC_VALUE", "FLOAT", "", "", "", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCData, "FOOTPRINT_ID", "LONG", "", "", "", "", "NULLABLE", "REQUIRED", "")
    arcpy.AddIndex_management(COCData, "GRID_ID", "CDAT_GRD_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AddIndex_management(COCData, "COC_NAME", "CDAT_NAM_IDX", "NON_UNIQUE", "NON_ASCENDING")

    # Create contaminant inventory table
    arcpy.CreateTable_management(geoDB, "COC_INVENTORY", "", "")

    # Add fields and indexes to contaminant inventory table
    arcpy.AddField_management(COCInvent, "COC_NAME", "TEXT", "", "", "20", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCInvent, "COC_UNITS", "TEXT", "", "", "20", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCInvent, "COC_QMDOC", "TEXT", "", "", "25000", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "COC_XML", "TEXT", "", "", "600", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "COC_NOTES", "TEXT", "", "", "20", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "INPUT_LAYER_NAME", "TEXT", "", "", "50", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "FILTER_LAYER_NAME", "TEXT", "", "", "50", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "STAT_TYPE", "TEXT", "", "", "20", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "LOG_TRANSFORM", "TEXT", "", "", "5", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "MIN_DIST", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "AVG_DIST", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "MAX_DIST", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "NNRATIO", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "NNZSCORE", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "NNPVALUE", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "SAINDEX", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "SAZSCORE", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "SAPVALUE", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "INTERP_LAYER_NAME", "TEXT", "", "", "50", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCInvent, "INTERP_TYPE", "TEXT", "", "", "5", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddIndex_management(COCInvent, "COC_NAME", "CDAT_NAM_IDX", "NON_UNIQUE", "NON_ASCENDING")

    # Create site attribute table
    arcpy.CreateTable_management(geoDB, "SITE_ATTRIBUTES", "", "")

    # Add fields to site attribute table...
    arcpy.AddField_management(SiteAttr, "GRID_ID", "LONG", "", "", "", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(SiteAttr, "HABITAT_ID", "TEXT", "", "", "50", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(SiteAttr, "CONDITION_ID", "TEXT", "", "", "2", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(SiteAttr, "REMEDIATION_ID", "TEXT", "", "", "50", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(SiteAttr, "SUBSITE_ID", "TEXT", "", "", "50", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(SiteAttr, "DEPTH_ID", "TEXT", "", "", "20", "", "NON_NULLABLE", "REQUIRED", "")
    arcpy.AddIndex_management(SiteAttr, "GRID_ID", "SATT_GRD_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AddIndex_management(SiteAttr, "HABITAT_ID", "SATT_HID_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AddIndex_management(SiteAttr, "CONDITION_ID", "SATT_CID_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AddIndex_management(SiteAttr, "REMEDIATION_ID", "SATT_RID_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AddIndex_management(SiteAttr, "SUBSITE_ID", "SATT_SID_IDX", "NON_UNIQUE", "NON_ASCENDING")
    arcpy.AssignDefaultToField_management(SiteAttr, "HABITAT_ID", "NA")
    arcpy.AssignDefaultToField_management(SiteAttr, "CONDITION_ID", "NA")
    arcpy.AssignDefaultToField_management(SiteAttr, "REMEDIATION_ID", "NA")
    arcpy.AssignDefaultToField_management(SiteAttr, "SUBSITE_ID", "NA")
    arcpy.AssignDefaultToField_management(SiteAttr, "DEPTH_ID", "NA")

    # Create footprints table
    arcpy.CreateTable_management(geoDB, "FOOTPRINTS", "", "")

    # Add fields to footprints table
    arcpy.AddField_management(Footprint, "GRID_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(Footprint, "SCENARIO_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(Footprint, "COC_NAME", "TEXT", "", "", "20", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(Footprint, "FOOTPRINT_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    
    arcpy.AddMessage("Created analysis database "+geoDB)
    arcpy.AddMessage("Updating project attributes...")
    rows = arcpy.InsertCursor(prjAttr)
    row = rows.newRow()
    if analystName is not None:
        row.ANALYST = str(analystName)
    rows.insertRow(row)
    del row
    del rows

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
