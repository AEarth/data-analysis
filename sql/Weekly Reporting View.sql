USE [VADam]
GO

CREATE view [dbo].[v_WeeklyReport] as

select 
	b.IdNumber, 
	b.Name as 'Dam Name',
	h.name as HazardClass,
	e.UserName as 'Regional Engineer',
	CONCAT('R',b.RegionalEngineerId) as Region,
	m.Name as County,
	c.Name as 'Event Type',
	d.Name as 'Enforcement Type',
	a.Description,
	a.NumberOfPeople as 'Number of People Involved',
	a.isEpExercised as 'EAP Exercised',
	a.LossOfLife as 'Loss of Life',
	a.CreatedDate as 'Reported Date',
	a.EventDate as 'Event Date'
	
from dam.DocumentedEvent a
left join dam.DamStructure b on b.id = a.damid
left join dam.DocumentedEventType c on c.Id = a.DocumentedEventTypeId
left join dam.EnforcementType d on d.id = a.EnforcementTypeId
left join [Security].[User] e on e.id = a.createdby

Left Join dam.HazardClassification H on H.id = b.HazardClassificationId

left join dam.IntersectedMunicipality m on m.SpatialDataContainerId = b.SpatialDataContainerId
and left(b.IdNumber,3) = case when len(m.FIPScode) = 1 then ('00'+m.FIPScode)
							  when len(m.FIPScode) = 2 then ('0'+m.FIPScode)
							  else m.FIPScode end



where a.CreatedDate > '8/27/2020' --and c.Name = 'General Narrative'

UNION ALL

select
	b.IdNumber,
	b.name as 'Dam Name',
	h.name as HazardClass,
	c.UserName as 'Regional Engineer',
	CONCAT('R',b.RegionalEngineerId) as Region,
	m.Name as County,
	'Event Type' = 'General Narrative',
	'Enforcement Type' = NULL,
	a.Narrative as 'Description',
	'Number of People Involved'=NULL,
	'EAP Exercised'=NULL,
	'Loss of Life'=NULL,
	a.createdDate as 'Reported Date',
	a.EventDate as 'Event Date'

from dam.GeneralNarrative a
left join dam.DamStructure b on b.id = a.damid
left join [Security].[User] c on c.id = a.createdby

Left Join dam.HazardClassification H on H.id = b.HazardClassificationId

left join dam.IntersectedMunicipality m on m.SpatialDataContainerId = b.SpatialDataContainerId
and left(b.IdNumber,3) = case when len(m.FIPScode) = 1 then ('00'+m.FIPScode)
							  when len(m.FIPScode) = 2 then ('0'+m.FIPScode)
							  else m.FIPScode end


----where b.idnumber !='099031' --and [Event Type] = 'General Narrative'


--GO


GO


