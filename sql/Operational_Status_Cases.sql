USE [VADam]
GO

/****** Object:  View [dbo].[v_Regulatory]    Script Date: 11/3/2022 1:24:05 PM ******/
SET ANSI_NULLS ON
GO

--if insp (h6.Name) = satisfactory or fair and certificate = regular then "Normal Operations"
--if insp = none and certificate = none then Not Applicable
--if certificate = conditional and alteration permit = active then "Under Remediation"
--if certificate = conditional then "Under Investigation, Planning, Permitting, or Design for Remediation"
--if inspection = poor or unsatifactory and operational status not "Enforcement Pending/Ongoing" then "Under Investagation, Planning, Permitting, Or Design for Remediation"


--Certificate Type	Last Conditional Assessment	Permit Type	Permit Expiration Date


SET QUOTED_IDENTIFIER ON
GO
 select top 4000
	a.id, 
	a.IdNumber, 

	a.Name as 'Dam Name', 
	i3.Name as 'Certificate Type', 
	n3.StatusText as 'Certificate Status', 
	case when h6.Name IS NOT NULL then h6.Name else 'Not Rated' end as 'Last Conditional Assessment',
	--a.TopHeight as 'Top Height', 
	--a.TopCapacity as 'Top Capacity', 
	b.Name as 'Hazard Class', 
	c.Name as 'Regulated', 
	CASE
		when r1.Name = ('Enforcement Pending/Ongoing') then 'Enforcement Pending/Ongoing'
		when h6.Name in ('Fair', 'Satisfactory') and i3.Name = 'Regular Operation and Maintenance Certificate' and CAST(m2.ExpirationDate as date) > CAST(GETDATE()as date) then 'Normal Operations'
		when h6.Name is Null and i3.Name is Null then 'Not Applicable'
		when i3.Name like 'Conditional%' and CAST(k.approvaldate as date) > CAST(DATEADD(YEAR,-4,(GETDATE())) as date) then 'Under Remediation'
		when i3.Name like 'Conditional%' then 'Under Investigation, Planning, Permitting, or Design for Remediation'
		when h6.Name  in ('Poor', 'Unsatisfactory') and r1.Name not like 'Enforcement Pending/Ongoing' then 'Under Investigation, Planning, Permitting, or Design for Remediation'	
		
		ELSE 'Status Not Estimated'
	END as 'Auto_OpStatus',

	r1.Name as 'Operational Status',
	a.RegionalEngineerId as 'Region', 

	d.Name as 'Regional Engineer', 

	m2.ExpirationDate as 'Regular Certificate Expiration',

	m3.ApprovalDate as'Certificate Approval', 
	m3.ExpirationDate as 'Certificate Expiration',
	h.[Regulatory Agency], 
	k.Name as 'Permit Type', 
	k.approvaldate as 'Permit Approval Date', 
	k.expirationdate as 'Permit Expiration Date', 


	q1.SLDLST as 'VA House District'

from dam.DamStructure a

join dam.HazardClassification b on b.id = a.HazardClassificationId
left join dam.DamRegulated c on c.Id = a.RegulatedId
join dam.RegionalEngineer d on d.Id = a.RegionalEngineerId

left join dam.IntersectedMunicipality e on e.SpatialDataContainerId = a.SpatialDataContainerId
and left(a.IdNumber,3) = case when len(e.FIPScode) = 1 then ('00'+e.FIPScode)
							  when len(e.FIPScode) = 2 then ('0'+e.FIPScode)
							  else e.FIPScode end

/**Identify Most Recent Conditional Certificate**/
left join (select damid, max(ExpirationDate) as 'Certificate Expiration'
from dam.CertificateApplication
where workflowstepid IN (49,50) and certificatetypeid in (18,19)
group by DamId) f on f.DamId = a.Id

left join dam.CertificateApplication m on m.damID=f.damID and m.ExpirationDate=f.[Certificate Expiration]
left join dam.CertificateType i on i.id = m.CertificateTypeId
left join dam.WorkflowStep n on n.Id = m.WorkflowStepId

/**Identify Most Recent Regular Certificate**/
left join (select damid, max(ExpirationDate) as 'Certificate Expiration'
from dam.CertificateApplication
where workflowstepid IN (49,50) and certificatetypeid in (1)
group by DamId) f2 on f2.DamId = a.Id

left join dam.CertificateApplication m2 on m2.damID=f2.damID and m2.ExpirationDate=f2.[Certificate Expiration]
left join dam.CertificateType i2 on i2.id = m2.CertificateTypeId
left join dam.WorkflowStep n2 on n2.Id = m2.WorkflowStepId

/**Identify Most Recent Certificate**/
left join (select damid, max(ApprovalDate) as 'Certificate Approval'
from dam.CertificateApplication
where workflowstepid IN (49,50)
group by DamId) f3 on f3.DamId = a.Id

left join dam.CertificateApplication m3 on m3.damID=f3.damID and m3.ApprovalDate=f3.[Certificate Approval]
left join dam.CertificateType i3 on i3.id = m3.CertificateTypeId
left join dam.WorkflowStep n3 on n3.Id = m3.WorkflowStepId

/**Identify Most Recent Inspections Owner**/
left join (select damid, max(InspectionDate) as 'Last Owner Inspection'
from dam.Inspection
where InspectionTypeId = 8 and WorkflowStepId IN (42,43)
group by DamId) g on g.DamId = a.Id

left join (select damid, inspectiondate, overallconditionid
from dam.inspection 
where InspectionTypeId = 8) h1 on h1.damid = g.damid and g.[Last Owner Inspection] = h1.inspectiondate

left join dam.overallcondition h2 on h2.id = h1.overallconditionID

/**Identify Most Recent Inspections PE**/
left join (select damid, max(InspectionDate) as 'Last Engineer Inspection'
from dam.Inspection
where InspectionTypeId = 9 and WorkflowStepId IN (42,43)
group by DamId) r on r.DamId = a.Id

left join (select damid, inspectiondate, overallconditionid
from dam.inspection
where InspectionTypeId = 9) h3 on h3.damid = r.damid and r.[Last Engineer Inspection] = h3.inspectiondate

left join dam.overallcondition h4 on h4.id = h3.overallconditionID

/**Regulatory Agency**/
left join (select a.DamId, b.Name as 'Regulatory Agency'
from dam.DamToFedAgency a
join dam.Agency b on b.id = a.AgencyId
where a.Regulatory = 1) h on h.DamId = a.id

/**Identify Most Recent Permit**/
left join (
	select a.DamId,c.Name,b.ApprovalDate,b.ExpirationDate 
	from(
	(select damid, max(expirationdate) as 'Last Permit' from dam.PermitApplication group by DamID) a
	left join (select Damid, ApprovalDate, ExpirationDate, PermitTypeId from dam.PermitApplication) b on b.damID=a.damID and b.ExpirationDate=a.[Last Permit]
	left join (select id, name from dam.PermitType) c on c.id = b.PermitTypeID)
	group by a.DamId,c.Name,b.ApprovalDate,b.ExpirationDate) k on k.DamId=a.id

/**Spillway Design Data**/
left join (select a.Id, a.Measure, b.Name as 'Design Unit'
from dam.DesignMeasure a
left join dam.DesignMeasureUnits b on b.id = a.UnitId) o on o.Id = a.AvlSpillwayCapacityMeasureId

left join (select a.Id, a.Measure, b.Name as 'Design Unit'
from dam.DesignMeasure a
left join dam.DesignMeasureUnits b on b.id = a.UnitId) p on p.Id = a.ReqSpillwayCapacityMeasureId

left join (select a.Id, a.Measure, b.Name as 'Design Unit'
from dam.DesignMeasure a
left join dam.DesignMeasureUnits b on b.id = a.UnitId) q on q.Id = a.IDAReductionMeasureId

/**Identify Most Recent Emergency Plan**/
left join (select a2.DamID, max(a.ExpirationDate) as 'EP Expiration' 
from dam.EmergencyPlan a
join dam.damstructuretoemergencyplan a2 on a2.eapid = a.id
where WorkflowStepId IN (37,38)
group by a2.DamId) s on s.DamId = a.Id

left join (select a.ExpirationDate, a2.DamId, a.eaptypeid, a.WorkflowStepId, a.AttachmentDirectoryId, 
	a.CntDownstreamDwellings,
	a.CntDownstreamSchools,
	a.CntDownstreamHospital,
	a.CntDownstreamBusiness,
	a.CntDownstreamRailroads,
	a.CntDownstreamUtilities,
	a.CntDownstreamParks,
	a.CntDownstreamGolfCourses,
	a.CntDownstreamTrails,
	a.CntDownstreamEmgInfrastructure,
	a3.[Count],
	a3.[Distance],
	a.RainfallAmtStage3Hr6,
	a.RainfallAmtStage3Hr12,
	a.RainfallAmtStage3Hr24,
	a.RainfallAmtStage2Hr6,
	a.RainfallAmtStage2Hr12,
	a.RainfallAmtStage2Hr24,
	a.RainfallAmtStage1Hr6,
	a.RainfallAmtStage1Hr12,
	a.RainfallAmtStage1Hr24,
	case when a4.Street2 IS NOT NULL then a4.Street+', '+a4.Street2+', '+a4.City+', '+a4.[State]+', '+a4.ZipCode
		 else a4.Street+', '+a4.City+', '+a4.[State]+', '+a4.ZipCode end as 'E911 Address',
	a.E911AddressDescription

from dam.EmergencyPlan a
join dam.damstructuretoemergencyplan a2 on a2.eapid = a.id
left join dam.Address a4 on a4.id=a.E911AddressId

left join (select EAPID, Count(RouteNumber) as 'Count', avg(cast(LengthAffected as decimal(10,2))) as 'Distance'
from dam.AffectedRoad 
group by EAPID) a3 on a3.EAPID = a.id) t on t.damID=s.damID and t.ExpirationDate=s.[EP Expiration]

left join dam.EAPType u on u.id = t.EAPTypeId
left join dam.WorkflowStep v on v.Id = t.WorkflowStepId

/**Identify DBIZ Attachments**/ 
left join(
select damid, max(CreatedDate) as 'maxdate'
from dam.Study
where StudyTypeId IN (1,3) and WorkflowStepId IN (13,14)
group by DamId) x on x.DamId=a.Id

/**Identify PMP Attachments**/
left join (select damid, max(CreatedDate) as 'maxdate'
from dam.Study
where StudyTypeId=2 and WorkflowStepId IN (13,14)
group by DamId) y on y.DamId=a.Id

/**Identify Emergency Plan Attachments**/
left join (select count(a.AttachmentTypeId) as 'EP Count', a.AttachmentDirectoryId, c2.DamId
from dam.Attachment a
join dam.EmergencyPlan c on c.AttachmentDirectoryId = a.AttachmentDirectoryId
join dam.DamStructureToEmergencyPlan c2 on c2.EAPId = c.id
where a.AttachmentTypeId IN (2,45)
group by a.AttachmentDirectoryId, c2.DamId) a1 on a1.AttachmentDirectoryID=t.AttachmentDirectoryId

/**Identify Certificate Attachments**/
left join (select max(a.AttachmentDirectoryId) as 'MaxAttachmentDirectoryID', a.AttachmentTypeId, b.Name as 'Certificate Attachment', c.DamId
from dam.Attachment a
left join dam.AttachmentType b on b.Id = a.AttachmentTypeId
	
join dam.CertificateApplication c on c.AttachmentDirectoryId = a.AttachmentDirectoryId
join (select max(d.ExpirationDate) as 'MaxExpire', d.DamId from dam.CertificateApplication d
	group by DamId) d on d.MaxExpire=c.ExpirationDate and d.damid = c.DamId
where a.AttachmentTypeId IN (39,40)
group by a.AttachmentTypeId, b.Name, c.DamId) b1 on b1.MaxAttachmentDirectoryID=m.AttachmentDirectoryId

left join dam.damsize c1 on c1.ID = a.SizeId

/**Identify Inundation Zone GIS Data Available**/
left join v_InundationZones e1 on e1.InvNum = a.IdNumber

left join v_Watersheds f1 on f1.InvNum = a.IdNumber

left join dam.city g1 on g1.ID = a.NearestCityId

left join v_EmergencyDrills j1 on j1.DamId = a.id

left join v_EmergencyTableTop k1 on k1.DamId = a.id

left join (select a.damid,
				  case when b.Organization IS NULL then b.FirstName+' '+b.LastName
					   else b.Organization+'-'+b.FirstName+' '+b.LastName end as 'Primary Contact',
				  c.Name as 'Primary Contact Type',
				  d.Email as 'Primary Contact Email',
			      e.Number as 'Primary Contact Phone',
				  case when g.street2 IS NULL then g.Street+', '+g.city+', '+g.[State]+' '+g.ZipCode
					   else g.Street+', '+g.Street2+', '+g.city+', '+g.[State]+' '+g.ZipCode end as 'Primary Contact Mailing Address'

	from dam.DamToContact a
	left join dam.Contact b on b.Id = a.ContactId
	left join dam.DamContactType c on c.Id = a.contacttypeid
	left join (select email, contactid
			   from dam.ContactEmailAddress 
			   where isPrimary=1) d on d.ContactId = b.id
	left join (select number, ContactId
			   from dam.ContactPhoneNumber
			   where isPrimary=1) e on e.ContactId = b.id
	left join (select addressid, contactid
			   from dam.ContactAddress 
			   where isprimary=1) f on f.ContactId = b.id
	left join dam.Address g on g.Id = f.AddressId
	where a.IsPrimary=1) l1 on l1.DamId = a.Id

left join ImpactRoadsGIS n1 on n1.InvNum = a.IdNumber
Left join (select* from ImpactStructuresGIS where Cat like 'Primary') o1 on o1.InvNum = a.IdNumber
left join (select invnum, sum(COUNT_OBJECTID) as 'All Structures Impacted Count GIS'
		   from ImpactStructuresGIS
		   group by InvNum) p1 on p1.InvNum = a.IdNumber

left join DamPointIntersects q1 on q1.idnumber = a.IdNumber

left join dam.OperationalStatus r1 on r1.id=a.OperationalStatusId

/**Identify Most Recent Inspections**/
left join (select damid, max(InspectionDate) as 'Last Inspection'
from dam.Inspection 
where overallconditionid IS NOT NULL--and where WorkflowStepId IN (42,43)
group by DamId) r3 on r3.DamId = a.Id

left join (select damid, inspectiondate, overallconditionid
from dam.inspection) h5 on h5.damid = r3.damid and r3.[Last Inspection] = h5.inspectiondate

left join dam.overallcondition h6 on h6.id = h5.overallconditionid

where a.Idnumber not Like '099031' and c.Name = 'Regulated'

GO


