#!/usr/bin/env python3
#
# Playground for GnuCash reports on top of sqlite db
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
import sys

from pathlib import Path
from os.path import exists


# DB_PATH = '../sqlitedb'
DB_EXT  = 'gnucash'

EXCLUDE_TRANS = []

pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
pd.set_option('display.min_rows', 100)
pd.set_option('display.expand_frame_repr', True)
pd.options.display.float_format = '{:,.2f}'.format

parser = argparse.ArgumentParser(description='Balans och resultat.')
parser.add_argument(dest='dbfile', type=ascii,
                    action='store',
                    help='Database file to use')
parser.add_argument(dest='company', type=ascii,
                    action='store',
                    help='Database file to use')
parser.add_argument(dest='year', type=ascii,
                    action='store',
                    help='Database file to use')
args = parser.parse_args()

DB_FILE = args.dbfile.strip("'")
COMPANY = args.company.strip("'")
YEAR = args.year.strip("'")
#DB_FILE = f'{DB_PATH}/{YEAR}/{COMPANY}_{YEAR}.{DB_EXT}'

if not exists(DB_FILE):
    sys.exit(f'ERROR: {DB_FILE} does not exits')


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

ek = dfb[dfb["code"]<2000].sum()[1]
tillg = dfb[(dfb["code"]>=2000) & (dfb["code"]<3000)].sum()[1]

print(f'EK:\t\t\t{ek:,.2f}\nTillgångar:\t\t{tillg:,.2f}\nBeräknat resultat:\t{ek+tillg:,.2f}')
print(f'')


print('\n************************** Resultatkonton ***********************************')
dft = df[df['code']>2999]
dfr = dft[['code','value']].groupby(['code']).sum().reset_index()
df['value'] = pd.to_numeric(df['value'])
print(dfr.columns)
print(dfr.head(100))
dfr.to_csv(f'{COMPANY}_{YEAR}-resultat.csv', index=False)
print(f'Beräknat resultat:{dfr["value"].sum():,.2f} (<0 innebär vinst)')


print('\n************************** SIE (alpha - experiment) ***********************************')

print('\nDropping rows without account code\n', df[df['code'].isnull()])
df = df[df['code'].notnull()]

df['code'] = df['code'].astype(int)
df.post_date = df.post_date.str.replace('-','')
df.enter_date = df.enter_date.str.replace('-','')
prev_num = -1
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
                    row['post_date'][0:8],
                    row['description'][0],
                    row['enter_date'][0:8])
    res = res + '#TRANS {} {{}} {:.2f} \"\" \"\" 0\n'.format(
            row['code'],
            row['value'])
    prev_num = row['num']

res = res + '}\n'

# Add SIE header to file
header = Path(f'{COMPANY}_header.se').read_text()
print('\nAdding SIE header to SIE file\n', header)
res = header + res

file = open(f'{COMPANY}_{YEAR}.se', 'w')
file.write(res)
file.close()
