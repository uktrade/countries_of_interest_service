from etl.etl import ETLTask

sql = '''
with level_2 as (
  select id, parent_id, segment from metadata_sector where level = 2
), level_1 as (
  select id, parent_id, segment from metadata_sector where level = 1
), level_0 as (
  select id, segment from metadata_sector where level = 0
), level_012 as (
  select 
    l2.id,
    concat(l0.segment, ':', l1.segment, ':', l2.segment) as segment
  
  from level_2 l2 join level_1 l1 on l2.parent_id = l1.id
    join level_0 l0 on l1.parent_id = l0.id
    
), level_01 as (
  select
    l1.id,
    concat(l1.segment, ':', l0.segment) as segment
    
  from level_1 l1 join level_0 l0 on l1.parent_id = l0.id
  
), segments as (
    select id, segment from level_0 union
    select id, segment from level_01 union
    select id, segment from level_012
)

select distinct
  company_number as companies_house_company_number,
  z.iso_alpha2_code as country_id,
  y.segment,
  'datahub_order' as source,
  l.id as source_id,
  l.created_on as timestamp

from order_order l join company_company r on l.company_id=r.id
  join metadata_country z on l.primary_market_id = z.id
  join segments y on l.sector_id = y.id

where company_number is not null
  and company_number != ''

order by 1

'''

table_fields = '''(
    companies_house_company_number varchar(12), 
    country_of_interest_id varchar(12), 
    sector_segment varchar(50), 
    source varchar(50), 
    source_id varchar(100),
    timestamp timestamp,
    primary key (companies_house_company_number, country_of_interest_id, source, source_id)
)'''

table_name = 'countries_and_sectors_of_interest_by_companies_house_company_number'

class Task(ETLTask):

    def __init__(self, sql=sql, table_fields=table_fields, table_name=table_name, *args, **kwargs):
        super().__init__(
            sql=sql,
            table_fields=table_fields,
            table_name=table_name,
            *args,
            **kwargs
        )