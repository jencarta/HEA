# ---------------------------------------------------------------------------
# NAME: LoadUnfilteredContaminantSurfaces.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: LoadUnfilteredContaminantSurfaces <input_analysis_database> <list_of_surfaces>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#   list_of_surfaces - List of interpolated surfaces to load into database
#
# Description: Loads an unfiltered interpolated raster surface into a single data table
#              for further data analysis.  Also updates associated metadata table and
#              for the raster surfaces
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: October 26, 2010
# Date Modified: June 1, 2011       - Edited for Arc 10.0 functionality
#                September 15, 2012 - Additional bug fixes
#                March 10, 2014     - Updated to arcpy 10.2 for V2.0
#
# ---------------------------------------------------------------------------

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

try:
    # Report version...
    ver = ARD_HEA_Tools.version()
    arcpy.AddMessage("ARD HEA Tools Version: " + ver)

    # Script arguments...
    geoDB = sys.argv[1]
    COCRaster = sys.argv[2]
    COCName = sys.argv[3]
    COCUnits = sys.argv[4]
    COCMetadata = sys.argv[5]
    COCStat = sys.argv[6]

    # Local variables...
    currDir = os.path.dirname(geoDB)
    COCInvent = geoDB + "\\COC_INVENTORY"

    # Set the geoprocessing environment
    env.overwriteOutput = 1

    # Setup raster variables
    COCRasterN = COCRaster.strip("'")
    COCRasterName = COCRasterN.split(os.sep)[-1]
    arcpy.AddMessage("raster name: " + COCRasterName)
    # COCExtract = geoDB + "\\" + COCRasterName + "_extract"
    COCExtract = geoDB + "\\" + COCName + "_extract"
    COCTable = COCName + "_tbl"
    currentdir = os.path.dirname(geoDB)

    # Remove any previous interpolated surfaces...
    desc = arcpy.Describe(COCRaster)
    if desc.DataType == "RasterLayer":
        COCLayerBase = COCLayer.split(os.sep)[-1]
    else:
        COCLayerBase = desc.Basename
        
    UNFLayer = "UNF_" + COCLayerBase
    UNFRaster = geoDB + "\\UNF_" + COCLayerBase
    # if arcpy.Exists(geoDB + "\\UNF_" + COCLayerBase):
    if arcpy.Exists(UNFRaster):
        arcpy.Delete_management(UNFRaster)

    # Import raster into analysis geodatabase
    arcpy.CopyRaster_management(COCRaster, UNFRaster)
    
    # Update inventory table
    rows = arcpy.UpdateCursor(COCInvent, "[COC_NAME] = '" + COCName + "'")
    row = rows.next()
    if row:
        row.COC_NAME = COCName
        if COCUnits is not None:
            row.COC_UNITS = COCUnits
        if COCStat is not None:
            row.STAT_TYPE = COCStat
        row.COC_NOTES = "Unfiltered Raster"
        row.INTERP_LAYER_NAME = COCLayerBase
        if arcpy.Exists(COCMetadata):
            f = open(COCMetadata, "r")
            qmText = f.read()
            f.close()
            row.COC_QMDOC = qmText
        rows.updateRow(row)
    else:    
        rows = arcpy.InsertCursor(COCInvent)
        row = rows.newRow()
        row.COC_NAME = COCName
        if COCUnits is not None:
            row.COC_UNITS = COCUnits
        if COCStat is not None:
            row.STAT_TYPE = COCStat
        row.COC_NOTES = "Unfiltered Raster"
        row.INTERP_LAYER_NAME = COCLayerBase
        if arcpy.Exists(COCMetadata):
            f = open(COCMetadata, "r")
            qmText = f.read()
            f.close()
            row.COC_QMDOC = qmText
        rows.insertRow(row)
    
    # Process: Remove existing records in COC Data table...
    arcpy.AddMessage("\nRemove any pre-existing " + COCName + " records from data tables...")
    arcpy.MakeTableView_management(geoDB + "\\COC_DATA", "COC_DATA_view", "[COC_NAME] = '" + COCName + "'")
    arcpy.DeleteRows_management("COC_DATA_view")
        
    # Process: Extract Values to Points...
    arcpy.AddMessage("Preparing " + COCName + " data..." + COCExtract)
    arcpy.ExtractValuesToPoints_sa(geoDB + "\\ANALYSIS_PNTS", COCRaster, COCExtract, "NONE", "VALUE_ONLY")

    # Process: Add Fields...
    arcpy.AddField_management(COCExtract, "COC_NAME", "TEXT", "", "", "20", "", "NULLABLE", "REQUIRED", "")
    arcpy.AddField_management(COCExtract, "COC_VALUE", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(COCExtract, "FOOTPRINT_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Process: Calculate Fields...
    rows = arcpy.UpdateCursor(COCExtract)
    row = rows.next()
    while row:
        row.COC_NAME = COCName
        row.COC_VALUE = row.RASTERVALU
        rows.updateRow(row)
        row = rows.next()
    del row
    del rows

    # Process: Delete Fields...
    arcpy.DeleteField_management(COCExtract, "RASTERVALU")

    # Process: Make Table View...
    filter_exp = "[COC_VALUE] >= 0"
    arcpy.TableToTable_conversion(COCExtract, geoDB, COCTable, filter_exp)

    # Process: Append to COC Data Table...
    arcpy.AddMessage("Updating table with " + COCName + " data...")
    InTable = geoDB + "\\" + COCTable
    arcpy.Append_management(InTable, geoDB + "\\COC_DATA", "NO_TEST")
    arcpy.Delete_management(InTable)

    # Process: Update Metadata Tables...
    history = ARD_HEA_Tools.get_process_history(currDir, COCExtract)
    rows = arcpy.UpdateCursor(COCInvent, "[COC_NAME] = '" + COCName + "'")
    row = rows.next()
    if row:
        if history is not None and history != "":
            xmltxt = row.COC_XML
            if xmltxt is not None:
                row.COC_XML = xmltxt + history
            else:
                row.COC_XML = history
            rows.updateRow(row)
    else:
        arcpy.AddMessage("\n***WARNING***\nError updating metadata record")
    del row
    del rows

    # Process: Make feature layer
    arcpy.MakeRasterLayer_management(UNFRaster, UNFLayer, "", "", "")

    # Set ouptut geoprocessing history
    ARD_HEA_Tools.set_process_history(currDir, UNFRaster, history)

    # Process: Compact database
    arcpy.Compact_management(geoDB)
    
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

