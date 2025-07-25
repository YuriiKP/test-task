import pandas as pd 

from airflow import DAG 
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator



sql1_1 = '''
with sales as (
	select fis.productkey, 
		   fis.salesamount,
		   fis.orderdatekey
	  from factinternetsales fis
	 union all 
	select frs.productkey, 
		   frs.salesamount,
		   frs.orderdatekey
	  from factresellersales frs
)

select s.productkey,
	   dp.englishproductname,
	   sum(s.salesamount)  
  from sales s
  join dimproduct dp
    on s.productkey = dp.productkey
  join dimdate dd
    on s.orderdatekey = dd.datekey
 where dd.calendarquarter = 4
   and dd.calendaryear = 2010
 group by s.productkey, dp.englishproductname
 order by sum(s.salesamount); 
'''

sql1_2 = '''
select fis.customerkey,
	   fis.orderdate,
       dc.firstname,
       dc.lastname
  from factinternetsales fis
  join dimdate dd 
    on fis.orderdatekey = dd.datekey
  join dimcustomer dc 
    on fis.customerkey = dc.customerkey
 where dd.calendaryear = 2013
   and dd.calendarsemester = 1
 order by dc.firstname; 
'''

sql1_3 = '''
select fsr.resellerkey,
	   dr.resellername,
	   sum(fsr.resellerkey * fsr.orderquantity) totalscount
  from factresellersales fsr
  join dimdate dd 
    on fsr.orderdatekey = dd.datekey
  join dimreseller dr
    on fsr.resellerkey  = dr.resellerkey
 where dd.calendarquarter = 2
   and dd.calendaryear = 2012
 group by fsr.resellerkey, dr.resellername
having sum(fsr.resellerkey * fsr.orderquantity) > 1000
 order by totalscount desc
'''

sql1_4 = '''
with sales as (
	select fis.productkey, 
		   fis.salesamount,
		   fis.orderdate
	  from factinternetsales fis
	 union all 
	select frs.productkey, 
		   frs.salesamount,
		   frs.orderdate
	  from factresellersales frs
),

salescategory as (
	select dc.englishproductcategoryname,
		   s.orderdate, 
	       sum(salesamount) salesamountcategory
	  from sales s
	  join dimproduct dp
	    on s.productkey = dp.productkey
	  join dimproductsubcategory dsc 
	    on dp.productsubcategorykey = dsc.productsubcategorykey
	  join dimproductcategory dc
	    on dsc.productcategorykey = dc.productcategorykey
	 where dsc.productcategorykey = 1
	 group by s.orderdate, dc.englishproductcategoryname
	 order by s.orderdate
)


select sc.*,
	   sum(sc.salesamountcategory) over (order by sc.orderdate) cumulatesum
  from salescategory sc
'''


def sales_report():
    URI = 'postgresql://postgres:secret@localhost:5430/postgres'
    total_sales_by_product = pd.read_sql(sql1_1, URI)
    total_sales_by_product.to_csv('results/1_total_sales_by_product.csv')

    active_customers = pd.read_sql(sql1_2, URI)
    active_customers.to_csv('results/2_active_customers.csv')

    high_volume_sellers = pd.read_sql(sql1_3, URI)
    high_volume_sellers.to_csv('results/3_high_volume_sellers.csv')

    sales_by_category = pd.read_sql(sql1_4, URI)
    sales_by_category.to_csv('results/4_sales_by_category.csv')


def log_analysis(): 
    # Читаем файл и разделяем его на строки
    with open('openssh.log', 'r', encoding='UTF-8') as f_obj:
        logs = f_obj.read()

    s_logs = logs.split('\n')
    
    # Если строка содержит 'Failed password for root from
    failed_pass = {}
    for sub_str in s_logs:
        if 'Failed password for root from' in sub_str: 
            ip = re.search('([0-9]{1,3}[\\.]){3}[0-9]{1,3}', sub_str) # Находим ip адреса в строке
            ip_str = ip.group()

            # Сохраняем в словарь
            if ip_str in failed_pass.keys():
                failed_pass[ip_str] = failed_pass[ip_str] + 1
            else:
                failed_pass[ip_str] = 1


    print(failed_pass)



with DAG(
    'some_dag',
    schedule_interval='@daily',
    start_date=days_ago(1),
    max_active_runs=1,
    concurrency=1,
) as dag:
    
    s_report = PythonOperator(
        task_id='ales_report',
        python_callable=sales_report
    )

    log = PythonOperator(
        task_id='log_analysis',
        python_callable=log_analysis
    )
    

    s_report >> log