import pandas as pd
from utils.sql import execute_query, query_database

def create_table(connection, fields, table_name):
    sql = ''' create table if not exists {} {} '''.format(table_name, fields)
    execute_query(connection, sql)

def drop_table(connection, table_name):
    sql = ''' drop table if exists {table_name} '''.format(table_name=table_name)
    execute_query(connection, sql)

def insert_data(df, output_connection, table_name):
    sql = '''insert into {} values'''.format(table_name)
    for i, values in enumerate(df.get_values()):
        # quote string values
        values = ["'{}'".format(val) if type(val) in [str, pd.Timestamp] else val  for val in values]
        values = ['Null' if pd.isnull(val) else val for val in values]
        sql += '\n\t({})'.format(', '.join(values))
        sql += ', ' if i != len(df) - 1 else ''
    sql += '\n\ton conflict do nothing'
    execute_query(output_connection, sql)
    
class ETLTask:

    def __init__(
            self,
            input_connection,
            output_connection,
            sql,
            table_fields,
            table_name,
            drop_table=False
    ):
        self.input_connection = input_connection
        self.output_connection = output_connection
        self.drop_table = drop_table
        self.sql = sql
        self.table_fields = table_fields
        self.table_name = table_name

    def __call__(self):
        if self.drop_table is True:
            print('\033[31mdropping table: {}\033[0m'.format(self.table_name))
            drop_table(self.output_connection, self.table_name)

        print('\033[31mcreate table: {}\033[0m'.format(self.table_name))
        create_table(self.output_connection, self.table_fields, self.table_name)

        print('\033[31mextract data\033[0m')
        df = query_database(self.input_connection, self.sql)
        print(df.head())

        print('\033[31mingest data\033[0m')
        insert_data(df, self.output_connection, self.table_name)

        print('\033[31mcheck data\033[0m')
        sql = ''' select * from {} limit 5 '''.format(self.table_name)
        df = query_database(self.output_connection, sql)
        print(df.head())

        print('\033[31mcheck data size\033[0m')
        sql = ''' select count(1) from {} '''.format(self.table_name)
        df = query_database(self.output_connection, sql)
        print('{} rows'.format(df.values[0][0]))