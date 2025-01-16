-- BEFORE RUNNING:
--create dir: D:\DSIS_Downloads\DBIZ_GIS. Create Hig Sig Low subdirs
--change lastRun date to equal the last quarter's run date

USE VADam
DECLARE @outPutPath varchar(50) = 'D:\DSIS_Downloads\DBIZ_GIS'
 ,@lastRun date = '2023-12-14'
, @i bigint
, @init int
, @data varbinary(max)
, @fPath varchar(max) 
, @folderPath  varchar(max)
  
--Get Data into temp Table variable so that we can iterate over it
DECLARE @DownloadTable TABLE (id int identity(1,1), [atid] bigint, [damid] bigint, [idnumber]  varchar(100) , [Hazard] varchar(3), [FileName]  varchar(500), [FileBinary] varBinary(max), [UploadedDate] DateTime2(7), WFStatus varchar(100))
  
INSERT INTO @DownloadTable([atid],[damid],[idnumber],[Hazard],[FileName],[FileBinary], [UploadedDate], [WFStatus])
Select at.id, ds.id, ds.[Idnumber],LEFT(h.name, 3) AS [Hazard] ,at.[FileName],at.[FileBinary], at.[UploadedDate], wf.StatusText
    from dam.attachment at
    left join Dam.Study s on s.AttachmentDirectoryId=at.AttachmentDirectoryId
    left join Dam.DamStructure ds on ds.Id = s.DamId
    left join Dam.HazardClassification h on h.Id = ds.HazardClassificationId
	left join dam.workflowstep wf on wf.id = s.WorkflowStepId


--Update 'Not In' statement with output from 'Existing GIS Dam ID List.sql' also need to add the list of faulty data
 where at.AttachmentTypeId = 113 --and at.id not in(67824,67608,67286,67137,66981,66849,66840,66443,66279,65909,65719,65701,65538,59582,60396,60379,64909,41547,58107,63028,62849,62805,62784,24139,41945,62055,62010,61911,61442,60944,60940,24146,60594,60457,54330,15124,60209,59991,58452,59720,64367,67054,58284,59481,58284,58558,59440,59447,59433,59440,59157,59127,59030,59447,59433,65486,28454,62884,58368,33636,33645,33654,58083,56904,58155,57229,60931,57764,49017,47039,66234,44456,65591,63929,43378,62164,39274,42667,35203,38658,35134,65112,31999,31820,31762,31713,36899,44825,60318,59691,23526,21609,58944,58948,58946,58946,18174,16633,16030,28552)
 and at.UploadedDate>@lastRun
 
 
select [damid],[idnumber],[Hazard],[FileName], cast([UploadedDate] as date) as 'UploadDate', WFStatus from @DownloadTable

---- Break here, Copy table to excel --------	
----- Then run download script: -----

SELECT @i = COUNT(1) FROM @DownloadTable
  
WHILE @i >= 1
BEGIN
 
    SELECT
     @data = [FileBinary],
     @fPath = @outPutPath + '\'+ [Hazard] + '\' +[idnumber]+'_'+[FileName]+'_'+ [atid]
     --@folderPath = @outPutPath
    FROM @DownloadTable WHERE id = @i
  
  --Manually Create folder first
  --EXEC  [dbo].[CreateFolder]  @folderPath
    
  EXEC sp_OACreate 'ADODB.Stream', @init OUTPUT; -- An instace created
  EXEC sp_OASetProperty @init, 'Type', 1; 
  EXEC sp_OAMethod @init, 'Open'; -- Calling a method
  EXEC sp_OAMethod @init, 'Write', NULL, @data; -- Calling a method
  EXEC sp_OAMethod @init, 'SaveToFile', NULL, @fPath, 2; -- Calling a method
  EXEC sp_OAMethod @init, 'Close'; -- Calling a method
  EXEC sp_OADestroy @init; -- Closed the resources
  
  print 'Document Generated at - '+  @fPath  
 
--Reset the variables for next use
SELECT @data = NULL 
, @init = NULL
, @fPath = NULL 
--, @folderPath = NULL
SET @i -= 1
END