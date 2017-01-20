# ---------------------------------------------------------------------------
# NAME: SliceContaminantSurface.py
# Version: 2.0 (ArcGIS 10.2)
# Author: Research Planning, Inc.
#
# Usage: SliceContaminantSurface <input_analysis_database> <input_threshold_table>
#
# Required Arguments: 
#   input_analysis_database - Name of analysis geodatabase
#   input_threshold_table - Name and location of table containing contaminant thresholds
#
# Description: Reclass contaminant surfaces based on information contained in 
#              contaminant threshold table
#
# Notes:  Currently the tool is designed to only be run via the ARD HEA Toolbox.
#
# Date Created: March 7, 2010
#
# Date Modified: March 8, 2010      - Use COC_INVENTORY table to determine raster to reclass
#                June 1, 2011       - Edited for Arc 10.0 functionality
#                September 15, 2012 - Additional bug fixes
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
    resDB = sys.argv[2]

    # Local variables...
    inTbl = resDB + "\\USER_Contaminant_Injury_Thresholds"
    usrTbl = geoDB + "\\USER_THRESHOLDS"
    tmpTbl = geoDB + "\\TEMP_THRES"
    catList = ["A", "B", "C", "D", "E", "F"]
    COCInvent = geoDB + "\\COC_INVENTORY"

    # Set the geoprocessing environment
    env.overwriteOutput = 1

    # Process: Import contaminant threshold table...
    if arcpy.Exists(usrTbl):
        arcpy.Delete_management(usrTbl)
    arcpy.TableToTable_conversion(inTbl, geoDB, "USER_THRESHOLDS")

    # Process: Loop through each record in contaminant threshold table...
    rows = arcpy.SearchCursor(usrTbl)
    row = rows.next()
    while row:
        # Check for name of interpolated surface for contaminant...
        rowsCOCInvent = arcpy.SearchCursor(COCInvent, "[COC_NAME] = '" + row.COC_NAME + "'")
        rowCOCInvent = rowsCOCInvent.next()
        if rowCOCInvent:
            inRaster = geoDB + "\\" + rowCOCInvent.INTERP_LAYER_NAME
            
            # Process: Check to see if raster layer exists
            if arcpy.Exists(inRaster):
                result = arcpy.GetRasterProperties_management(inRaster, "MINIMUM")
                rasMIN = float(result.getOutput(0))
                result = arcpy.GetRasterProperties_management(inRaster, "MAXIMUM")
                rasMAX = float(result.getOutput(0))
                
                # Process: Create temporary table used to reclass contaminant...
                arcpy.AddMessage("Preparing data to reclass the " + row.COC_NAME + " contaminant surface: " + inRaster + " for scenario " + str(row.Scenario_ID))
                if arcpy.Exists(tmpTbl):
                    arcpy.Delete_management(tmpTbl)
                arcpy.CreateTable_management(geoDB, "TEMP_THRES", "", "")
                arcpy.AddField_management(tmpTbl, "FROM_VALUE", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(tmpTbl, "TO_VALUE", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(tmpTbl, "LABEL", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                
                # Process: Update temporary table with values for reclass
                crows = arcpy.InsertCursor(tmpTbl)
                errFlag = False
                recs = 0
                for cat in range(6):
                    skipFlag = False
                    crow = crows.newRow()
                    if cat != 5:
                        high = row.getValue("Thres_" + catList[cat] + "_High")
                        if high > rasMAX:
                            high = rasMAX
                    else:
                        high = rasMAX
                    if cat != 0:
                        prevhigh = row.getValue("Thres_" + catList[cat-1] + "_High")
                    else:
                        prevhigh = 0
                    perc = row.getValue("Thres_" + catList[cat] + "_Perc")                         
                    if high is None or perc is None:
                        errFlag = True
                    if prevhigh >= high:
                        skipFlag = True        
                    if high < rasMIN:
                        skipFlag = True
                    if prevhigh > rasMAX:
                        skipFlag = True
                    crow.FROM_VALUE = prevhigh
                    crow.TO_VALUE = high
                    crow.LABEL = int(perc)
                    if not skipFlag:
                        crows.insertRow(crow)
                        recs = recs + 1
                        arcpy.AddMessage("Level: " + str(catList[cat])+" from: " + str(prevhigh) + " to: " + str(high) + " Pct Injury: " + str(perc) )
                    else:
                        arcpy.AddMessage("Skipping level: "+ str(catList[cat]))
                del crow
                del crows
                
                # Process: Reclass contaminant...
                if not errFlag and recs > 0:
                    arcpy.AddMessage("Reclassifying surface...\n")
                    outRaster = geoDB + "\\" + ARD_HEA_Tools.sanitizetext(str.upper(str(row.COC_NAME))) + "_SC" + str(row.Scenario_ID)
                    outPolygon = geoDB + "\\" + ARD_HEA_Tools.sanitizetext(str.upper(str(row.COC_NAME))) + "_SC" + str(row.Scenario_ID) + "_ZONE"
                    if arcpy.Exists(outRaster):
                        arcpy.Delete_management(outRaster)
                    if arcpy.Exists(outPolygon):
                        arcpy.Delete_management(outPolygon)
                    arcpy.ReclassByTable_sa(inRaster, tmpTbl, "FROM_VALUE", "TO_VALUE", "LABEL", outRaster, "NODATA")
                    arcpy.RasterToPolygon_conversion(outRaster, outPolygon, "SIMPLIFY")
                else:
                    arcpy.AddMessage("Cannot reclass: " + row.COC_NAME + " for scenario: " + str(row.Scenario_ID))
                    arcpy.AddMessage("Missing or incorrect values in threshold table.\n")

                #Process: Remove temporary table used by reclass
                arcpy.Delete_management(tmpTbl)
                
            else:
                arcpy.AddMessage("\nCannot reclass: " + row.COC_NAME + " for scenario: " + str(row.Scenario_ID))
                arcpy.AddMessage("Contaminant surface does not exist.\n")
        else:
            arcpy.AddMessage("\nCannot reclass: " + row.COC_NAME + " for scenario: " + str(row.Scenario_ID))
            arcpy.AddMessage("Contaminant surface does not exist.\n")
        del rowCOCInvent
        del rowsCOCInvent
        row = rows.next()
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

