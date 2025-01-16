import arcpy
from arcpy import env
import os, re
# Set the workspace for the ListFeatureClass function
arcpy.env.overwriteOutput = True
arcpy.env.outputMFlag = "Disabled"
arcpy.env.outputZFlag = "Disabled"
def ScriptTool(mergedzones, newzonesfolder):
    SRSobj = arcpy.Describe(mergedzones).spatialReference
    arcpy.AddMessage(SRSobj.name)
    to_sr = SRSobj
    folder = os.path.basename(newzonesfolder)
    arcpy.AddMessage("Input folder: "+ folder)
    
    invnum = folder.split("_")[0]
    arcpy.AddMessage("Inventory Number: "+ invnum)
    #FUNCTION SUB DEFINITIONS
    #Converts file names to include InvNum be compatible with gdb
    def cleanname(filevar):
        fname, ext = os.path.splitext(filevar)
        arcpy.AddMessage(fname)
        cleanname.simplename = re.sub('[\W_]+', '', fname)
        arcpy.AddMessage(cleanname.simplename)
        cleanname.dname = "P_" + invnum +"_" + cleanname.simplename
        cleanname.pname = "D_" + invnum + "_" + cleanname.simplename
    #GP: Project Dissolve Append
    def projectdissolveappend(fnamevar, pnamevar, dnamevar):
        arcpy.Project_management(fnamevar, pnamevar, to_sr)
        arcpy.Dissolve_management(pnamevar, dnamevar, "", "", "MULTI_PART", "DISSOLVE_LINES")
        arcpy.Append_management(dnamevar, mergedzones, schema_type="NO_TEST")
    
    #PROCEDURE
    for root, dirs, filenames in os.walk(newzonesfolder):
        for filename in filenames:      
            if filename.endswith(".shp"):
                file = os.path.join(root, filename)
                arcpy.AddMessage(file)
                desc = arcpy.Describe(file)
                if desc.shapeType == "Polygon":
                    arcpy.AddMessage(f"Polygon: {file}")
                    cleanname(filename)
                    projectdissolveappend(file, cleanname.pname,cleanname.dname)
                elif desc.shapeType == "Polyline":
                    arcpy.AddMessage(f"PolyLINE: {file}")
                    cleanname(filename)
                    f2pname = "va" + cleanname.simplename + "_2poly"
                    arcpy.AddMessage("Attempting to convert to polygon...")
                    arcpy.FeatureToPolygon_management(file, f2pname)
                    projectdissolveappend(f2pname, cleanname.pname,cleanname.dname)
    return
# This is used to execute code if the file was run but not imported
if __name__ == '__main__':
    # Tool parameter accessed with GetParameter or GetParameterAsText
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    
    ScriptTool(param0, param1)
    
    # Update derived parameter values using arcpy.SetParameter() or arcpy.SetParameterAsText()
