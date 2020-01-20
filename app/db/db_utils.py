import sys
import traceback

import pandas as pd
import sqlalchemy
import sqlalchemy.exc
from sqlalchemy.schema import CreateSchema

from app.db.models import sql_alchemy

SCHEMAS = ['public', 'admin', 'algorithm']


def execute_query(query, data=None, df=True, raise_if_fail=False):
    result_set = execute_statement(query, data, raise_if_fail)
    rows = result_set.fetchall()
    if df:
        return pd.DataFrame(rows, columns=result_set.keys())
    return rows


def execute_statement(stmt, data=None, raise_if_fail=False):
    connection = sql_alchemy.engine.connect()
    transaction = connection.begin()
    try:
        status = connection.execute(stmt, data)
        transaction.commit()
        connection.close()
        return status
    except sqlalchemy.exc.ProgrammingError as err:
        transaction.rollback()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("error:")
        traceback.print_tb(exc_traceback, file=sys.stdout)
        # exc_type below is ignored on 3.5 and later
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        print(err)
        if raise_if_fail:
            raise err
        connection.close()


def table_exists(table_name, schema='public', materialized_view=False):
    _from = 'information_schema.tables' if not materialized_view else 'pg_matviews'
    _where = 'table_schema' if not materialized_view else 'schemaname'
    _and = 'table_name' if not materialized_view else 'matviewname'

    query = f"""
     SELECT EXISTS (
        SELECT 1
           FROM   {_from}
           WHERE  {_where} = '{schema}'
           AND    {_and} = '{table_name}'
     );
    """
    return list(execute_statement(query))[0][0]


def drop_table(fq_name):
    stmt = f'DROP TABLE IF EXISTS {fq_name} CASCADE'
    execute_statement(stmt)


def rename_table(table_name_1, table_name_2):
    sql = f'alter table {table_name_1} rename to {table_name_2}'
    execute_statement(sql)


def create_table(fields, table_name):
    sql = f'create table if not exists {table_name} {fields}'
    execute_statement(sql)


def create_index(index, table_name, index_name=None):
    index_name = index_name if index_name else '{}_index'.format(table_name)
    index_str = '(' + ','.join(index) + ')'
    sql = f'create index if not exists {index_name} on {table_name} {index_str}'
    execute_statement(sql, data=index)


def insert_data(df, table_name):
    if len(df):
        sql = '''
            insert into {table_name} ({columns})
            values ({values}) on conflict do nothing
        '''.format(
            table_name=table_name,
            columns=','.join(df.columns),
            values=','.join(['%s' for i in range(len(df.columns))]),
        )
        for col in df.columns:
            if df[col].dtype == '<M8[ns]':
                df[col] = df[col].map(lambda x: None if pd.isnull(x) else x.isoformat())
        execute_statement(sql, df.values.tolist(), raise_if_fail=True)


def dsv_buffer_to_table(
    csv_buffer,
    table,
    schema='public',
    has_header=False,
    null='',
    sep='\t',
    columns=None,
    quote=None,
    encoding=None,
    reraise=False,
):
    connection = sql_alchemy.engine.raw_connection()
    cursor = connection.cursor()
    fq_table_name = f'"{schema}"."{table}"'
    sql = _get_sql_copy_statement(
        fq_table_name, columns, has_header, sep, null, quote, encoding
    )
    try:
        cursor.copy_expert(sql, csv_buffer)
        connection.commit()
    except Exception as err:


        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("error:")
        traceback.print_tb(exc_traceback, file=sys.stdout)
        # exc_type below is ignored on 3.5 and later
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        print(err)
        if reraise is True:
            raise err
    cursor.close()
    connection.close()


def _get_sql_copy_statement(
    table, columns, has_header, delimiter, null_value, quote, encoding
):
    sql = 'COPY {}'.format(table)
    if columns:
        sql += ' ({})'.format(','.join(columns))
    sql += ' FROM STDIN WITH CSV'
    if has_header:
        sql += ' HEADER'
    if delimiter:
        sql += " DELIMITER E'{}'".format(delimiter)
    if null_value:
        sql += " null as '{}'".format(null_value)
    if quote:
        sql += " QUOTE \'{}\'".format(quote)
    if encoding:
        sql += f" ENCODING '{encoding}'"
    return sql


def create_schemas(engine):
    for schema_name in SCHEMAS:
        _create_schema_if_not_exists(engine, schema_name)


def _create_schema_if_not_exists(engine, schema_name):
    if not engine.dialect.has_schema(engine, schema_name):
        engine.execute(CreateSchema(schema_name))
