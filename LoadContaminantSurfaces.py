# ---------------------------------------------------------------------------
# NAME: LoadContaminantSurfaces.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: LoadContaminantSurfaces <input_analysis_database> <list_of_surfaces>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#   list_of_surfaces - List of interpolated surfaces to load into database
#
# Description: Loads interpolated raster surfaces into a single data table for further
#              data analysis.  Also updates associated metadata table for the raster
#              surfaces
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: February 3, 2010
# Date Modified: March 8, 2010      - Consolidated ANALYSIS_TABLE and COC_INVENTORY tables
#                June 1, 2011       - Edited for Arc 10.0 functionality
#                September 15, 2012 - Additional bug fixes
#                January 2, 2013    - Removed 9.3 python instantiation to avoid "ExtractValuesToPoints" bug
#                March 7, 2014      - Updated arcpy to 10.2 for V2.0
#                March 10, 2014     - Fixed error handling when data have not been filtered
#                March 5, 2015      - Added a check to see if contaminant surfaces match analysis grid
#                March 19, 2015     - Fixed and modified check above to just give a warning
#
# ---------------------------------------------------------------------------

class filtered(Exception):
    pass

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
    COCRasters = sys.argv[2]

    # Local variables...
    COCRasterList = [v.strip("'") for v in COCRasters.split(";")]
    currDir = os.path.dirname(geoDB)
    env.workspace = geoDB
    xmlDoc = currDir + "\\temp.xml"
    COCInvent = geoDB + "\\COC_INVENTORY"
    prjAttr = geoDB + "\\PROJECT_ATTRIBUTES"

    # Set the geoprocessing environment
    arcpy.overwriteOutput = 1

    # Process each surface
    for COCRaster in COCRasterList:

        # Setup Raster Variables
        desc = arcpy.Describe(COCRaster)
        if desc.DataType == "RasterLayer":
            COCRasterName = COCRaster.split(os.sep)[-1]
        else:
            COCRasterName = desc.Basename
        COCExtract = geoDB + "\\" + COCRasterName + "_extract"
        COCTable = COCRasterName + "_tbl"
        currentdir = os.path.dirname(geoDB)
        filename = currentdir + "\\temp.xml"
        
        # Check if COC has been updated in inventory table
        rows = arcpy.SearchCursor(COCInvent, "[INTERP_LAYER_NAME] = '" + COCRasterName + "'")
        COCField = "empty"
        row = rows.next()
        while row:
            COCField = row.COC_NAME
            row = rows.next()
        del row
        del rows
        if COCField == "empty":
            raise filtered

        # Process: Extract Values to Points...
        arcpy.AddMessage("Extracting " + COCField + " data from " + str(COCRasterName))
        arcpy.Copy_management(geoDB + "\\ANALYSIS_PNTS", COCExtract)
        ExtractMultiValuesToPoints(COCExtract, [[COCRaster, "COC_VALUE"]], "NONE")
        
        # Process: Check for NULL values in COCExtract and provide warning
        arcpy.MakeFeatureLayer_management(COCExtract, "COClyr")
        expression = arcpy.AddFieldDelimiters(COCExtract, "COC_VALUE") + " >= 0"
        arcpy.SelectLayerByAttribute_management("COClyr","NEW_SELECTION",expression)
        result = arcpy.GetCount_management("COClyr")
        COCcount = int(result.getOutput(0))
        cursor = arcpy.da.SearchCursor(prjAttr, ("TOTAL_CELLS"))
        row = cursor.next()
        countGridCells = row[0]
        if COCcount != countGridCells:
            arcpy.AddMessage("Warning: the number of contaminant surface cells: " + str(COCcount) + ", does not match the number of analysis grid cells: " + str(countGridCells))
        del row, cursor
           
        # Process: Remove existing records in COC Data table...
        arcpy.AddMessage("\nRemove any pre-existing " + COCField + " records from data tables...")
        rows = arcpy.UpdateCursor(geoDB + "\\COC_DATA", "[COC_NAME] = '" + COCField + "'")
        for row in rows:
            rows.deleteRow(row)
        del rows

        # Process: Add Fields...
        arcpy.AddField_management(COCExtract, "COC_NAME", "TEXT", "", "", "20", "", "NULLABLE", "REQUIRED", "")
        arcpy.AddField_management(COCExtract, "FOOTPRINT_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculate Fields...
        rows = arcpy.UpdateCursor(COCExtract)
        for row in rows:
            row.COC_NAME = COCField
            rows.updateRow(row)
        del row
        del rows

        # Process: Make Table View...
        filter_exp = "[COC_VALUE] >= 0"
        arcpy.TableToTable_conversion(COCExtract, geoDB, COCTable, filter_exp)

        # Process: Append to COC Data Table...
        arcpy.AddMessage("Updating COC value table with " + COCField + " data...")
        InTable = geoDB + "\\" + COCTable
        arcpy.Append_management(InTable, geoDB + "\\COC_DATA", "NO_TEST")
        arcpy.Delete_management(InTable)
    
except filtered:
    arcpy.AddError("\n*** ERROR ***\nInput features for raster layer " + COCRaster + " have not been filtered or entry is missing from COC_INVENTORY table")
    print "\n*** ERROR ***\nInput features for raster layer " + COCRaster + " have not been filtered or entry is missing from COC_INVENTORY table"
    
except arcpy.ExecuteError:
    # Get the geoprocessing error messages
    msgs = arcpy.GetMessage(0)
    msgs += arcpy.GetMessages(2)

    # Return gp error messages for use with a script tool
    arcpy.AddError(msgs)

    # Print gp error messages for use in Python/PythonWin
    print msgs
    
except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a 
    # message string
    pymsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)

    # Return python error messages for use with a script tool
    arcpy.AddError(pymsg)

    # Print Python error messages for use in Python/PythonWin
    print pymsg
   
