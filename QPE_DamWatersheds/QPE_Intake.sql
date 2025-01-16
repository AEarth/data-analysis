Truncate Table VADam.dbo.QPEPrep
GO

BULK INSERT VADam.dbo.QPEPrep
FROM 'D:\QPEReceive\QPEFile.csv'
WITH (
      FIRSTROW = 2,
	  FIELDTERMINATOR = ',',
      ROWTERMINATOR = '\n'
)
GO


Declare @CurrentDate [datetime]
select @CurrentDate = max([ISSUE_TIME])
from VADam.dbo.QPEPrep

Declare @LastDate [datetime]
select @LastDate = max([ISSUE_TIME])
from VADam.dbo.QPECurrent


If @CurrentDate > @LastDate

BEGIN
	insert into VADam.dbo.QPEMaster ([InvNum],[LegacyNumber],[FREQUENCY],[RainfallInches24],[RainfallInches12],[RainfallInches06],[ISSUE_TIME],[START_TIME])
	select InvNum,LegacyNumb,Frequency,RainfallIn,Rainfall_1,Rainfall_2,[ISSUE_TIME],[START_TIME]
	from VADam.dbo.QPEPrep

	insert into BMPTracking.dbo.OlapDSISQPE ([InvNum],[LegacyNumber],[FREQUENCY],[RainfallInches24],[RainfallInches12],[RainfallInches06],[ISSUE_TIME],[START_TIME])
	select InvNum,LegacyNumb,Frequency,RainfallIn,Rainfall_1,Rainfall_2,[ISSUE_TIME],[START_TIME]
	from VADam.dbo.QPEPrep


	Truncate Table VADam.dbo.QPECurrent

	insert into VADam.dbo.QPECurrent ([InvNum],[LegacyNumber],[FREQUENCY],[RainfallInches24],[RainfallInches12],[RainfallInches06],[ISSUE_TIME],[START_TIME])
	select InvNum,LegacyNumb,Frequency,RainfallIn,Rainfall_1,Rainfall_2,[ISSUE_TIME],[START_TIME]
	from VADam.dbo.QPEPrep


	truncate table BMPTracking.dbo.OlapDSISQPEEmergencyCurrent

	insert into BMPTracking.dbo.OlapDSISQPEEmergencyCurrent
	select*
	from VADam.dbo.v_QPEEmergencyCurrent

	truncate table BMPTracking.dbo.OlapDSISQPEGrid

	insert into BMPTracking.dbo.OlapDSISQPEGrid
	select*
	from VADam.dbo.v_QPEDSISGrid

END

ELSE

BEGIN	
	Print 'Date Error, No Upload Conducted'
END