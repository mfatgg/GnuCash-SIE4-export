#!/usr/bin/env python3
#
# GnuCash SIE4 export
#
# Resources
# * https://wiki.gnucash.org/wiki/SQL
#

tables = ['accounts',          'customers',         'lots',              'splits',
'billterms',         'employees',         'orders',            'taxtable_entries',
'books',             'entries' ,          'prices',            'taxtables',
'budget_amounts',    'gnclock',           'recurrences',       'transactions',
'budgets',           'invoices',          'schedxactions',     'vendors',
'commodities' ,      'jobs',              'slots',             'versions']

import sqlite3
import argparse
import pandas as pd

DB_PATH = '../sqlitedb'
DB_EXT  = 'gnucash'

EXCLUDE_TRANS = []

pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
pd.set_option('display.min_rows', 100)
pd.set_option('display.expand_frame_repr', True)
pd.options.display.float_format = '{:,.2f}'.format

parser = argparse.ArgumentParser(description='Balans och resultat.')
parser.add_argument(dest='year', type=ascii,
                    action='store',
                    help='År')
parser.add_argument(dest='company', type=ascii,
                    action='store',
                    help='Företag')
args = parser.parse_args()

COMPANY = args.company.strip("'")
YEAR = args.year.strip("'")

DB_FILE = f'{DB_PATH}/{YEAR}/{COMPANY}_{YEAR}.{DB_EXT}'
print(f'Report based on: {DB_FILE}')


# Read sqlite query results into a pandas DataFrame
def sel_table(table):
    print(f'\n-------------------- {table} -------------------\n')
    con = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f'select * from {table}', con)
    print(df.columns)
    print(df.head(100))
    con.close()
    return df

def run_sql(sql):
    con = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(sql, con)
    con.close()
    return df


df = run_sql('select * from transactions t, splits s, accounts a where t.guid=s.tx_guid and s.account_guid=a.guid order by num')
df = df[['num', 'post_date', 'enter_date', 'code', 'description', 'value_num', 'quantity_denom', 'account_type']]
df['num'] = pd.to_numeric(df['num'])
df['code'] = pd.to_numeric(df['code'])
df = df[~df['num'].isin(EXCLUDE_TRANS)]
df['value'] = df['value_num'] / df['quantity_denom']
df = df[['num', 'post_date', 'enter_date', 'code', 'description', 'account_type', 'value']]
df.to_csv(f'{COMPANY}_{YEAR}.csv', index=False)

print('\n************************** Balanskonton ***********************************')
dft = df[df['code']<3000]
dfb = dft[['code','value']].groupby(['code']).sum().reset_index()
print(dfb.columns)
print(dfb.head(100))
dfb.to_csv(f'{COMPANY}_{YEAR}-balans.csv', index=False)
print(f'Diff:{dfb["value"].sum()}')

print('\n************************** Resultatkonton ***********************************')
dft = df[df['code']>2999]
dfr = dft[['code','value']].groupby(['code']).sum().reset_index()
df['value'] = pd.to_numeric(df['value'])
print(dfr.columns)
print(dfr.head(100))
dfr.to_csv(f'{COMPANY}_{YEAR}-resultat.csv', index=False)
print(f'Beräknat resultat:{dfr["value"].sum()} (<0 innebär vinst)')


printnum = -1
first_trans = True
res = ''
df = df.sort_values('num')
for index, row in df.iterrows():
    if prev_num != row['num']:
        if not first_trans:
            res = res + '}\n'
        first_trans = False

        res = res + '#VER A {} {} \"{}\" {}\n{{\n'.format(
                    row['num'],
                    row['post_date'][0:10],
                    row['description'][0],
                    row['enter_date'][0:10])
    res = res + '#TRANS {} {{}} {:.2f} \"\" \"\" 0\n'.format(
            row['code'],
            row['value'])
    prev_num = row['num']

res = res + '}\n'

file = open(f'{COMPANY}_{YEAR}.se', 'w')
file.write(res)
file.close()
