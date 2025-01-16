import gzip, os, shutil, arcpy, urllib, os
#import time
#code to test run time
#starttime = time.time()

rootfolder = r"D:\Data\QPE"
gdb =  r"D:\Data\QPE\QPE_Working.gdb"
sourcegdb = r"D:\Data\QPE\DamData.gdb"
gdb_lastrun = "D:\Data\QPE\QPE_LastRun.gdb"
DLfolder = "GribDownloads"

arcpy.env.workspace=gdb
arcpy.env.overwriteOutput= True

#arcpy.env.outputCoordinateSystem = os.path.join(rootfolder, "GCS_Coordinate_System_imported_from_GRIB_file.prj")

def gdbname(file):
    return gdb+"\\"+ file

def sourcename(file):
    return sourcegdb+"\\"+file

def downloadname(file):
    return os.path.join(rootfolder,DLfolder, file)


#delete oldest run working gdb
if os.path.exists(gdb_lastrun):
   shutil.rmtree(gdb_lastrun)
   
#rename previous run to last run gdb
if os.path.exists(gdb):
   os.rename(gdb, gdb_lastrun)


###create new empty working gdb
arcpy.management.CreateFileGDB(rootfolder, "QPE_Working.gdb")


arcpy.CheckOutExtension("spatial")

urllib.urlretrieve("https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_06H/MRMS_RadarOnly_QPE_06H.latest.grib2.gz", downloadname("QPE06.grib2.gz"))
urllib.urlretrieve("https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_12H/MRMS_RadarOnly_QPE_12H.latest.grib2.gz", downloadname("QPE12.grib2.gz"))
urllib.urlretrieve("https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_24H/MRMS_RadarOnly_QPE_24H.latest.grib2.gz",  downloadname("QPE24.grib2.gz"))

print "Download Complete!"

with gzip.open(downloadname("QPE06.grib2.gz"), 'rb') as f_in:
    with open(downloadname("QPE06.grib2"), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
with gzip.open(downloadname("QPE12.grib2.gz"), 'rb') as f_in:
    with open(downloadname("QPE12.grib2"), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
with gzip.open(downloadname("QPE24.grib2.gz"), 'rb') as f_in:
    with open(downloadname("QPE24.grib2"), 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

print "Unzip Complete"


QPE24hr=downloadname("QPE24.grib2")
QPE12hr=downloadname("QPE12.grib2")
QPE06hr=downloadname("QPE06.grib2")


Watersheds=sourcename("DamWatersheds_Prj")
#Boundary="D:\QPE QPF\QPE\DamData.gdb\StatewideWithDamWatersheds"

#sp="D:\QPE QPF\QPE\WGS_1984_Web_Mercator_Auxiliary_Sphere.prj"
#sp2="D:\QPE QPF\QPE\GCS_Coordinate_System_imported_from_GRIB_file.prj"

QPE06_WSTab = os.path.join(gdb, "QPE06_WSTab")
QPE12_WSTab = os.path.join(gdb, "QPE12_WSTab")
QPE24_WSTab = os.path.join(gdb, "QPE24_WSTab")


#create two subsets of watersheds, ones large enough to intersect >=1 QPE point, and ones that will need a "near" spatial join. These two layers can stay constant as the 6km point grid will be the same accross all time periods
arcpy.Select_analysis(in_features=Watersheds, out_feature_class="DamWatersheds_int", where_clause="IntersectsField = 1")
arcpy.Select_analysis(in_features=Watersheds, out_feature_class="DamWatersheds_noint", where_clause="IntersectsField = 0")

#----6HR CALCS-----#
#6hr raster clip and point conversion (figure out how to get clip tighter)
#clip raster (rectangle bounding box around watersheds)
Clip_Extent = sourcename("Clip_ExtentMinumum")
arcpy.Clip_management(in_raster=QPE06hr, rectangle="-83.5957345849999 36.117826834 -75.442920327 39.393095789", out_raster="QPE6hr_Clip", in_template_dataset=Clip_Extent, nodata_value="9.999000e+003", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")

QPE6hr_pts = gdbname("QPE6hr_pts")
arcpy.RasterToPoint_conversion(in_raster="QPE6hr_Clip", out_point_features=QPE6hr_pts, raster_field="Value")

#Do both spatial join types for 6hr

QPE6hr_int = gdbname("QPE6hr_int")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_int", join_features=QPE6hr_pts, out_feature_class=QPE6hr_int, join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_int,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,Mean,#,QPE6hr_pts,grid_code,-1,-1', match_option="INTERSECT", search_radius="", distance_field_name="")
QPE6hr_noint = gdbname("QPE6hr_noint")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_noint", join_features=QPE6hr_pts, out_feature_class=QPE6hr_noint, join_operation="JOIN_ONE_TO_MANY", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_noint,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,First,#,QPE6hr_pts,grid_code,-1,-1', match_option="CLOSEST", search_radius="", distance_field_name="")

#Append 6hr results to one table
arcpy.Append_management(inputs=QPE6hr_noint, target=QPE6hr_int, schema_type="NO_TEST")

#6hr Field calcs
arcpy.AlterField_management(in_table=QPE6hr_int, field="grid_code", new_field_name="RainfallInches06", new_field_alias="RainfallInches06", field_type="DOUBLE", field_length="8", field_is_nullable="NULLABLE", clear_field_alias="false")
arcpy.CalculateField_management(in_table=QPE6hr_int, field="RainfallInches06", expression="round((!RainfallInches06!/25.4),1)", expression_type="PYTHON", code_block="")

print("6HR QPE Analysis Complete")

#----12HR CALCS-----#
#12hr raster clip and point conversion (figure out how to get clip tighter)
#clip raster (rectangle bounding box around watersheds)
arcpy.Clip_management(in_raster=QPE12hr, rectangle="-83.5957345849999 36.117826834 -75.442920327 39.393095789", out_raster="QPE12hr_Clip", in_template_dataset=Clip_Extent, nodata_value="9.999000e+003", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")


QPE12hr_pts = gdbname("QPE12hr_pts")
arcpy.RasterToPoint_conversion(in_raster="QPE12hr_Clip", out_point_features=QPE12hr_pts, raster_field="Value")

#Do both spatial join types for 12hr

QPE12hr_int = gdbname("QPE12hr_int")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_int", join_features=QPE12hr_pts, out_feature_class=QPE12hr_int, join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_int,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,Mean,#,QPE12hr_pts,grid_code,-1,-1', match_option="INTERSECT", search_radius="", distance_field_name="")

QPE12hr_noint = gdbname("QPE12hr_noint")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_noint", join_features=QPE12hr_pts, out_feature_class=QPE12hr_noint, join_operation="JOIN_ONE_TO_MANY", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_noint,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,First,#,QPE12hr_pts,grid_code,-1,-1', match_option="CLOSEST", search_radius="", distance_field_name="")

#Append 12hr results to one table
arcpy.Append_management(inputs=QPE12hr_noint, target=QPE12hr_int, schema_type="NO_TEST")

#12hr Field calcs
arcpy.AlterField_management(in_table=QPE12hr_int, field="grid_code", new_field_name="RainfallInches12", new_field_alias="RainfallInches12", field_type="DOUBLE", field_length="8", field_is_nullable="NULLABLE", clear_field_alias="false")
arcpy.CalculateField_management(in_table=QPE12hr_int, field="RainfallInches12", expression="round((!RainfallInches12!/25.4),1)", expression_type="PYTHON", code_block="")

print("12HR QPE Analysis Complete")

#----24hr CALCS-----#
#24hr raster clip and point conversion (figure out how to get clip tighter)
#clip raster (rectangle bounding box around watersheds)
arcpy.Clip_management(in_raster=QPE24hr, rectangle="-83.5957345849999 36.117826834 -75.442920327 39.393095789", out_raster="QPE24hr_Clip", in_template_dataset=Clip_Extent, nodata_value="9.999000e+003", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")


QPE24hr_pts = gdbname("QPE24hr_pts")
arcpy.RasterToPoint_conversion(in_raster="QPE24hr_Clip", out_point_features=QPE24hr_pts, raster_field="Value")

#Do both spatial join types for 24hr

QPE24hr_int = gdbname("QPE24hr_int")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_int", join_features=QPE24hr_pts, out_feature_class=QPE24hr_int, join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_int,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,Mean,#,QPE24hr_pts,grid_code,-1,-1', match_option="INTERSECT", search_radius="", distance_field_name="")

QPE24hr_noint = gdbname("QPE24hr_noint")
arcpy.SpatialJoin_analysis(target_features="DamWatersheds_noint", join_features=QPE24hr_pts, out_feature_class=QPE24hr_noint, join_operation="JOIN_ONE_TO_MANY", join_type="KEEP_ALL", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,DamWatersheds_noint,InvNum,-1,-1;grid_code "grid_code" true true false 8 Double 0 0 ,First,#,QPE24hr_pts,grid_code,-1,-1', match_option="CLOSEST", search_radius="", distance_field_name="")

#Append 24hr results to one table
arcpy.Append_management(inputs=QPE24hr_noint, target=QPE24hr_int, schema_type="NO_TEST")

#24hr Field calcs
arcpy.AlterField_management(in_table=QPE24hr_int, field="grid_code", new_field_name="RainfallInches24", new_field_alias="RainfallInches24", field_type="DOUBLE", field_length="8", field_is_nullable="NULLABLE", clear_field_alias="false")
arcpy.CalculateField_management(in_table=QPE24hr_int, field="RainfallInches24", expression="round((!RainfallInches24!/25.4),1)", expression_type="PYTHON", code_block="")

print("24hr QPE Analysis Complete")


#Join other periods to  to 24hr fc
arcpy.JoinField_management(in_data=QPE24hr_int, in_field="InvNum", join_table="QPE12hr_int", join_field="InvNum", fields="RainfallInches12")
arcpy.JoinField_management(in_data=QPE24hr_int, in_field="InvNum", join_table="QPE6hr_int", join_field="InvNum", fields="RainfallInches06")

#Create Final Table Template from Source GDB
arcpy.TableToTable_conversion(in_rows="QPE24hr_int", out_path=gdb, out_name="QPE_TablePrep", where_clause="", field_mapping='InvNum "InvNum" true true false 6 Text 0 0 ,First,#,QPE24hr_int,InvNum,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,QPE24hr_int,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,QPE24hr_int,Shape_Area,-1,-1;FREQUENCY "FREQUENCY" true true false 4 Long 0 0 ,First,#,QPE24hr_int,Join_Count,-1,-1;RainfallInches24 "RainfallInches24" true true false 8 Double 0 0 ,First,#,QPE24hr_int,RainfallInches24,-1,-1;RainfallInches12 "RainfallInches12" true true false 8 Double 0 0 ,First,#,QPE24hr_int,RainfallInches12,-1,-1;RainfallInches06 "RainfallInches06" true true false 8 Double 0 0 ,First,#,QPE24hr_int,RainfallInches06,-1,-1', config_keyword="")

TemplateTable = sourcename("QPE_TableTemplate")
arcpy.CreateTable_management(out_path=gdb, out_name="QPE_OutputTable", template="'{}'".format(TemplateTable), config_keyword="")

#append to template table
arcpy.Append_management(inputs="QPE_TablePrep", target="QPE_OutputTable", schema_type="NO_TEST", field_mapping='LegacyNumber "LegacyNumber" true true false 5 Text 0 0 ,First,#;InvNum "InvNum" true true false 6 Text 0 0 ,First,#,QPE_TablePrep,InvNum,-1,-1;Shape_Length "Shape_Length" true true false 4 Float 0 0 ,First,#,QPE_TablePrep,Shape_Length,-1,-1;Shape_Area "Shape_Area" true true false 4 Float 0 0 ,First,#,QPE_TablePrep,Shape_Area,-1,-1;FREQUENCY "FREQUENCY" true true false 4 Long 0 0 ,First,#,QPE_TablePrep,FREQUENCY,-1,-1;RainFallInches24 "RainFallInches24" true true false 4 Float 0 0 ,First,#,QPE_TablePrep,RainfallInches24,-1,-1;RainfallInches12 "RainFallInches12" true true false 4 Float 0 0 ,First,#,QPE_TablePrep,RainfallInches12,-1,-1;RainfallInches06 "RainfallInches06" true true false 4 Float 0 0 ,First,#,QPE_TablePrep,RainfallInches06,-1,-1;ISSUE_TIME "ISSUE_TIME" true true false 8 Date 0 0 ,First,#;START_TIME "START_TIME" true true false 8 Date 0 0 ,First,#', subtype="")

#calc Date Time
arcpy.CalculateField_management("QPE_OutputTable","ISSUE_TIME",'datetime.datetime.now()',"PYTHON")
arcpy.CalculateField_management("QPE_OutputTable","START_TIME",'datetime.datetime.now().replace(microsecond=0, second=0, minute=0)',"PYTHON")


#Master Database Append
#master="D:\DATA\QPE\MasterQPE.gdb\MasterQPETable"
#arcpy.Append_management("QPE_OutputTable",master,"NO_TEST")

#Create SFTP Output File
arcpy.TableToTable_conversion("QPE_OutputTable","D:\Data\QPEOutput","QPEFile.csv")

#endtime = time.time()
#elapsedtime = (endtime - starttime)/60
#print("Model run time: ", elapsedtime, " minutes") 
