NOAA Habitat Equivalency Analysis Tool 
Version 2.0

CONTENTS
==============================================================
Habitat equivalency analysis (HEA) has become an industry-standard analytical approach in natural resource damage assessment to quantify ecological injuries and scale compensatory restoration actions. To perform HEA calculations, trustees must determine how long the injury will persist, the relative service level of the injured and replacement resources, and the lifetime of the replacement project. NOAA’s HEA Tool performs an equivalency analysis designed to meet these needs.  The NOAA HEA Tool guides users through these steps using both ESRI (R)ArcGIS geographic information system (GIS) and Microsoft (R) Access software to:

- Access spatial datasets (e.g., datasets from Query Manager or DIVER), 
- Interpolate contaminant concentrations, 
- Define important site parameters,
- Input HEA parameters,
- conduct HEA analyses, and
- View and export a wide range of HEA results.


These files contain Microsoft Access databases, ArcGIS toolboxes and associated Python scripts, and associated files and documentation. 

To apply the Access-based NOAA HEA tools, users must be operating a Windows-based computer with Microsoft Access and ESRI ArcGIS.  Current versions of Windows supported include Windows XP and 7.   The Access-based tools have been tested in MS Access 2010 and 2013.  The GIS components of the tools are compatible with ArcGIS 10.0, 10.1 and 10.2 and require a valid license for the Spatial Analyst extension.  Initial trials indicate the tools should also be compatible with ArcGIS 10.3, but extensive compatibility testing has not been performed.  The database and GIS tools are configured for running with either a 32 or 64-bit processor.


CHANGES IN THIS VERSION
==============================================================

- None


KNOWN ISSUES
=============================================================

- None


INSTALLATION
==============================================================

The HEA Tools are distributed as a zip archive accompanying this text file.  This archive (NOAA_HEA_Tool_VX.X.zip) when unzipped establishes a folder structure at the installation location and unpacks all ArcGIS and MS Access tools to the correct locations within that folder structure.  The “X.X” in the file name will vary by tool version.  The zip archive will create a new master software folder called “/NOAA_HEA_Tool/” and a series of subfolders within.

The “Documentation” subfolder contains the project documentation.  The “GIS_Site_Creation_Tools” subfolder contains the tool components intended for use with ArcGIS including python scripts (.py and .pyc), an ArcGIS toolbox file (.tbx), metadata templates (.xml), an ArcGIS layer file (.lyr), and ArcGIS project file (.mxd). The “Projects” subfolder is empty but is intended to contain individual folders for each project generated using the ArcGIS tools. The “HEA_Calculation_Tool” subfolder contains the NOAA Access HEA Tool file (HEA Tool.mdb) and all the files required for the Access Tools to operate in the “DoNotRemove” subfolder.  Users should not move or alter any files in the “DoNotRemove” or “GIS_Site_Creation_Tools” subfolders. 

It is important to ensure that all tools are located in the folder structure as described above.  Failure to do so will cause errors for some processing steps. Note that the initial ArcGIS Tools that setup analysis geodatabases for a new project will automatically create a new project folder.  It is good practice to not include spaces or special characters in the name of these project folder or any other files. Though not required, it is recommended to install the “/NOAA_HEA_Tool/” folder at the root drive level (e.g. “C:/”). If a user is installing a newer version of these tools alongside an older version, the folder name can be changed if a previous version of “/NOAA_HEA_Tool/“folder is already present. 

To install the ArcGIS Tools, take the following steps:
1.)	Open ArcMap
2.)	Right-click on the background of the ArcToolbox window.
3.)	Select "Add Toolbox".
4.)	Navigate to the directory where these files were unzipped and select the "ARD HEA Tools.tbx" file.

The HEA Tools toolbox will then be available in the ArcToolbox window in either ArcMap or ArcCatalog.

The MS Access Tools do not require any additional installation steps.


ACKNOWLEDGEMENTS
==============================================================

The NOAA Habitat Equivalency Analysis (HEA) Tools were developed by NOAA Office of Response and Restoration, Assessment and Restoration Division (ARD), Industrial Economics, Incorporated (IEc), and Research Planning, Inc. (RPI), with funding from NOAA.

For additional information on the HEA Tools, please contact:

Benjamin Shorr
National Ocean Service
Office of Response and Restoration
Assessment and Restoration Division
7600 Sand Point Way NE, Seattle, WA 98115
(w) 206.526.4654 (c) 206.280.5336
benjamin.shorr@noaa.gov

