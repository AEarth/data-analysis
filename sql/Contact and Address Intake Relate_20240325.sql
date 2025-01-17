 USE VADAM
 GO

declare @contactid int
set @contactid = (select MAX(Id) FROM [VADam].[Dam].[Contact])

declare @addressid int
set @addressid = (select MAX(Id) FROM [VADam].[Dam].[Address])

declare @damtocontactid int
set @damtocontactid = (select MAX(Id)

begin transaction


INSERT INTO Dam.Contact (FirstName, LastName, Organization)

  SELECT
  [FirstName]
  ,[LastName]
  ,[Organization]
  FROM [dbo].[ContactsIntake_20240325_20230908]

  order by IdNumber asc


insert into Dam.Address(Street, Street2, City, State, Zipcode)

  select
    [Street],
	[Street2],
    [County],
    [State],
    [Zip]
    
  FROM [dbo].[ContactsIntake_20240325_20230908]
order by IdNumber asc


  insert into Dam.ContactAddress(ContactId, IsPrimary, AddressId)
  select
    ((ROW_NUMBER() OVER(ORDER BY IdNumber)) + @contactid ) AS 'ContactId'
    ,1
    ,((ROW_NUMBER() OVER(ORDER BY IdNumber)) + @addressid ) AS 'AddressId'

  from [dbo].[ContactsIntake_20240325_20230908]


  order by IdNumber asc


insert into Dam.DamToContact(DamId, ContactId, ContactTypeId, OwnerTypeId, IsPrimary)
select 
        ds.Id
        ,((ROW_NUMBER() OVER(ORDER BY intake.IdNumber)) + @contactid ) AS 'ContactId'
        ,2 --owner
        ,5 --private
        ,1 --yes primary
from [dbo].[ContactsIntake_20240325_20230908] intake
left join [VADam].dam.damstructure ds on intake.[IdNumber] = ds.[IdNumber]


insert into Dam.ContactToFederalAgency(DamToContactId, FedAgencyId)
select
    ((ROW_NUMBER() OVER(ORDER BY IdNumber)) + @damtocontactid ) AS 'DamToContactId'
    ,19 --not applicable
from [dbo].[ContactsIntake_20240325_20230908] intake


commit transaction
--rollback transaction