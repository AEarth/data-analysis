import arcpy
import os
from datetime import datetime
import logging


now = datetime.now()
today = now.strftime("%Y%m%d")

#setup logging
logfolder = r"D:\DamSafety\Logs"
logfile = os.path.join(logfolder,"DamPoints_"+today+".txt")

# Create a FileHandler explicitly so we can close it later
file_handler = logging.FileHandler(filename=logfile, mode='w+')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

# Add the file handler and a stream handler to the root logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler(sys.stdout))

logging.debug("Start Time")
#end logging setup

#gis env variables
arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = True 

ds_folder = r"D:\DamSafety"
gdb_run = os.path.join(ds_folder, f'DS_Proc_{today}.gdb')
gdb_prior = r"D:\DamSafety\DamSafety_Processing_prior.gdb"
gdb_proc = r"D:\DamSafety\DamSafety_Processing.gdb"
gdb_serv = r"D:\DamSafety\GIS_ServerData\data.gdb"
aprx = arcpy.mp.ArcGISProject(r"D:\DamSafety\GIS_ServerData\DamPoints_Map3_prep.aprx")


#names
attribute_view = "VADam.dbo.v_Regulatory_Portal"
query_table = "DamView_Regulatory_QueryTable"
native_table = "DamView_Regulatory_NativeTable"
sql_connection_file = r"D:\DamSafety\DB_Connections\dsreader_wsq07236.sde"

m = aprx.listMaps('Map')[0]
logging.debug(m)

try:
    #make a new file gdb and set as workspace. need this because os blocks using prior gdb
    arcpy.management.CreateFileGDB(ds_folder, f'DS_Proc_{today}')
    arcpy.env.workspace = gdb_run
    aprx.defaultGeodatabase = gdb_run
    #--remove 2nd run prep gdb and rename last run to prior gdb
    # if os.path.isdir(gdb_prior):
    #     os.remove(gdb_prior)
    #     logging.debug(f"Removing old gdb: {gdb_prior}")
    # if os.path.isdir(gdb_proc):
    #     os.rename(gdb_proc,gdb_prior)
    #     logging.debug(f"Renaming prior gdb: {gdb_proc}")
    #--grab dam points geometry from DamStructure Table
    arcpy.management.MakeQueryLayer(sql_connection_file, "DamPoints_sql", """SELECT ID, IdNumber,Geom
    FROM VADam.Dam.DamStructure where IdNumber != '099031'""", "ID", "POINT", "3857", 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]];-20037700 -30241100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision', "DEFINE_SPATIAL_PROPERTIES", "DO_NOT_INCLUDE_M_VALUES", "DO_NOT_INCLUDE_Z_VALUES", "-9304817.9352 4375749.2079 -8398282.5212 4777723.3394")
    logging.debug("Make Query Dam Points Layer from DamStructure Table")
    logging.debug(arcpy.GetMessages())


    #--grab attributes from Regulatory View
    arcpy.management.MakeQueryLayer(sql_connection_file, query_table, f"select * from {attribute_view}", "id", "POINT", '', None, "DEFINE_SPATIAL_PROPERTIES", "DO_NOT_INCLUDE_M_VALUES", "DO_NOT_INCLUDE_Z_VALUES", "0 0 0 0")
    logging.debug("Get Regulatory Attributes Table")
    logging.debug(arcpy.GetMessages())


    arcpy.conversion.TableToTable(
        in_rows="DamView_Regulatory_QueryTable",
        out_path=gdb_run,
        out_name=native_table,
        where_clause="",
        config_keyword=""
    )


    #sql spatial to native gis spatial
    sql2native_dampoints = os.path.join(gdb_run, "DamPoints_sql_f2Point") 
    arcpy.management.FeatureToPoint("DamPoints_sql", sql2native_dampoints, "CENTROID")
    logging.debug("Convert Dam Points Query Layer to Native GIS Spatial Layer")
    logging.debug(arcpy.GetMessages())


    arcpy.management.JoinField(sql2native_dampoints, "IdNumber", native_table, "IdNumber","LegacyNumber;DamName;OtherName;HazardClass;Regulated;RegAgency;DSRegion;RegionalEngineer;County;TopHeight;TopCapacity;latitude;longitude;CertType;CertStatus;CertApprvDate;CertExpDate;LastInspCondition;DBIZ_Attach;EP_Type;EP_Expiration;EP_Status;Owners;OwnerTypes;EAPStructureCount;PrimaryStructImpactCountGIS;RoadImpactCntGIS;damid;certID;LastInspCondVal;InspId;StructureCount;LastInspDate;LastDrillDate;LastTableTopDate;StudyType;DateSealed;IS_Status;IS_StatusDate;IS_GIS;EngineerName;Organization;IS_ContactID;PrimaryContact;DamType")
    logging.debug("Join Regulatory Attributes to Dam Points Layer")
    logging.debug(arcpy.GetMessages())


    arcpy.management.AddField(sql2native_dampoints, "Legend", "TEXT", None, None, 11, '', "NULLABLE", "NON_REQUIRED", '')
    logging.debug("Add Field for Hazard Legend")
    logging.debug(arcpy.GetMessages())

    arcpy.management.CalculateField(sql2native_dampoints, "Legend", "hazlegend(!HazardClass!)", "PYTHON3", """import re
def hazlegend(x):
    if re.search('High', x):
        return 'High'
    if re.search('Sig', x):
        return 'Significant'
    if re.search('Low', x):
        return "Low"
    else:
        return "Unknown" """, "TEXT", "NO_ENFORCE_DOMAINS")
                    
    logging.debug("Calculate Hazard Legend Field")
    logging.debug(arcpy.GetMessages())


    # fix city prefix to match VGIN County layer
    arcpy.management.CalculateField(sql2native_dampoints, "County", "fixcity(!County!)", "PYTHON3", """import re
def fixcity(x):
    if x is None:
        pass
    elif re.search('City of',x):
        z = re.sub('City of','', x)
        return z + ' City'
    else:
        return x""", "TEXT", "NO_ENFORCE_DOMAINS")
            
    logging.debug("Tweaking County / City Field to match VGIN County Layer")
    logging.debug(arcpy.GetMessages())
           

    #massage a field to match existing (can fix in sql view later)
    arcpy.management.AlterField(
        in_table="DamPoints_sql_f2Point",
        field="IS_ContactID",
        new_field_name="ContactID",
        new_field_alias="",
        field_type="LONG",
        field_length=5,
        field_is_nullable="NULLABLE",
        clear_field_alias="CLEAR_ALIAS"
    )

    #TRUNCATE DAM POINTS SOURCE
    dampoints_source = os.path.join(gdb_serv, "DamPoints")
    #arcpy.management.TruncateTable(dampoints_source)
    arcpy.DeleteRows_management(dampoints_source)
    logging.debug("Truncate DamPoints Server Source")
    logging.debug(arcpy.GetMessages())

    #APPEND
    arcpy.management.Append(sql2native_dampoints, dampoints_source, "NO_TEST", None, '', '')

    logging.debug("Append New DamPoints to Server Source")
    logging.debug(arcpy.GetMessages())

    #close logging
    logger.removeHandler(file_handler)
    file_handler.close()

except:
    logging.exception('Critical Error Exception raised')
    #close logging
    logger.removeHandler(file_handler)
    file_handler.close()
    raise




#SCHEMA CHANGE NOTE UPDATE VIEW TO MATCH PRIOR:
# LastInspCondition - InspCondition
# LastInspCondVal - InspCondVal
# LastInspDate - InspDate
# Organization - EngineerOrg
# ContactID - IS_ContactID