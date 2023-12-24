#!/usr/bin/env python3
#
# Playground for GnuCash reports on top of sqlite db
#
# SIE4-export assumes that verification with num 1 has initial balances
#
# Resources
# * https://wiki.gnucash.org/wiki/SQL
# * https://sietest.sie.se/

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
import codecs

from pathlib import Path
from os.path import exists


# DB_PATH = '../sqlitedb'
DB_EXT  = 'gnucash'

EXCLUDE_TRANS = []
MOMS_KONTON = [1650,2611,2612,2614,2641,2645,2650]


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
    con = sqlite3.connect(DB_FILE)
    print(f'\n-------------------- {table} -------------------\n')
    df = pd.read_sql_query(f'select * from {table}', con)
    print(df.columns)
    print(df.head(100))
    con.close()
    return df

def run_sql(sql):
    con = sqlite3.connect(DB_FILE)
    df = pd.read_sql(sql, con)
    con.close()
    return df


df = run_sql(
    'select'
    '   t.post_date, t.enter_date, t.description,'
    '   s.tx_guid, s.memo, s.value_num, s.quantity_denom,'
    '   a.name, a.account_type, a.code, i.id i_id, c.id c_id, v.id v_id'
    ' from transactions t, splits s, accounts a'
    '   left join invoices i'
    '     on i.post_txn=t.guid or i.post_lot=s.lot_guid or i.id=t.num'
    '   left join customers c'
    '     on i.owner_guid=c.guid'
    '   left join vendors v'
    '     on i.owner_guid=v.guid'
    ' where t.guid=s.tx_guid and s.account_guid=a.guid'
    ' order by post_date')
print ("df:", df.columns)
grouped = df.groupby(['tx_guid'])
print("orig df:")
for tx_guid, tx_df in grouped:
    print("  transaction:", tx_guid, tx_df.columns)


# Saw new-line in description once...
df = df.replace('\n','', regex=True)

df = df[['tx_guid', 'post_date', 'enter_date', 'code', 'description', 'memo', 'value_num', 'quantity_denom', 'account_type', 'name', 'i_id', 'c_id', 'v_id']]
#df['num'] = pd.to_numeric(df['num'])
df['code'] = pd.to_numeric(df['code'])

print('\nDropping rows without account code\n', df[df['code'].isnull()])
df = df[df['code'].notnull()]

#print('\nDropping rows without number \n', df[df['num'].isnull()])
#df = df[df['num'].notnull()]

df['code'] = df['code'].astype(int)
#df['num'] = df['num'].astype(int)
df['i_id'] = df['i_id'].fillna('')
df['c_id'] = df['c_id'].fillna('')
df['v_id'] = df['v_id'].fillna('')

#df = df[~df['num'].isin(EXCLUDE_TRANS)]
df['value'] = df['value_num'] / df['quantity_denom']
df = df[['tx_guid', 'post_date', 'enter_date', 'code', 'description', 'memo', 'account_type', 'value', 'name', 'i_id', 'c_id', 'v_id']]
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

# SIE4:
# #IB 0 1311 100000 0
# #UB 0 1311 100000 0

ib_ub = ''
#dft = df[df['num']==1]
dft = df.sort_values('post_date').groupby(['code']).first().reset_index()
for index, row in dft.iterrows():
    ib_ub = ib_ub + '#IB 0 {} {:.2f} 0\n'.format(
                  row['code'],
                  row['value'])

for index, row in dfb.iterrows():
    ib_ub = ib_ub + '#UB 0 {} {:.2f} 0\n'.format(
                  row['code'].astype(int),
                  row['value'])

print('\n************************** Resultatkonton ***********************************')
dft = df[df['code']>2999]
dfr = dft[['code','value']].groupby(['code']).sum().reset_index()
df['value'] = pd.to_numeric(df['value'])
print(dfr.columns)
print(dfr.head(100))
dfr.to_csv(f'{COMPANY}_{YEAR}-resultat.csv', index=False)
print(f'Beräknat resultat:{dfr["value"].sum():,.2f} (<0 innebär vinst)')

# SIE:
# #RES 0 3010 -400000 0
res_ = ''
for index, row in dft.iterrows():
    res_ = res_ + '#RES 0 {} {:.2f} 0\n'.format(
                  row['code'],
                  row['value'])



print('\n************************** MOMS-konton ***********************************')
dfM = df[df['code'].isin(MOMS_KONTON)]
dfM.loc[:,'month'] = pd.to_datetime(dfM['post_date'])
grouped  = dfM[['month','code','value']].groupby(['code',pd.Grouper(key='month', freq='M')])

dft = grouped.agg([('Debit' , lambda x : x[x > 0].sum()),('Kredit' , lambda x : x[x < 0].sum())])
print(dft)
dft.reset_index().to_csv(f'{COMPANY}_{YEAR}-moms.csv', index=False)

print('\n\n--- Totaler ---')
dft = grouped.sum()
print(dft)
dft.reset_index().to_csv(f'{COMPANY}_{YEAR}-moms-total.csv', index=False)




print('\n************************** SIE (alpha - experiment) ***********************************')

dfa = df[['code', 'name']].drop_duplicates('code').sort_values('code')
accounts = ''
for index, row in dfa.iterrows():
    accounts = accounts + '#KONTO {} \"{}\"\n'.format(
                  row['code'],
                  row['name'])

dim = '#DIM 8 Kund\n'
dim = '#DIM 9 Leverantör\n'
dim = '#DIM 10 Faktura\n'

df.post_date = df.post_date.str.replace('-','')
df.enter_date = df.enter_date.str.replace('-','')
prev_num = -1
res = ''

df = df.sort_values(['post_date', 'tx_guid', 'code'])
grouped = df.groupby(['post_date', 'tx_guid'])
for idx, (tx_guid, tx_df) in enumerate(grouped):
    first_trans = True
    for index, row in tx_df.iterrows():
        if first_trans:
            first_trans = False
            res = res + '#VER A {} {} \"{}\"\n{{\n'.format(
                        idx+1,
                        row['post_date'][0:8],
                        row['description'])
        invoice_obj = '\"10\" \"{}\"'.format(row['i_id']) if row['i_id'] else ''
        customer_obj = '\"8\" \"{}\"'.format(row['c_id']) if row['c_id'] else ''
        vendor_obj = '\"9\" \"{}\"'.format(row['v_id']) if row['v_id'] else ''
        objs = invoice_obj
        if customer_obj:
            if objs:
                objs += ' '
            objs += customer_obj
        if vendor_obj:
            if objs:
                objs += ' '
            objs += vendor_obj
        res = res + '#TRANS {} {{{}}} {:.2f} \"\" \"{}\"\n'.format(
                row['code'],
                objs,
                row['value'],
                row['memo'])
    res = res + '}\n'


# Add SIE header to file
header = Path(f'{COMPANY}_header.se').read_text()
print('\nAdding SIE header to SIE file\n', header)

res = header + '\n' + accounts + '\n' + ib_ub + '\n' + res_ + '\n'+ res

filename = f'{COMPANY}_{YEAR}.se'
file = open(filename, 'w')
file.write(res)
file.close()

try:
    nfo = codecs.open(filename, encoding='utf-8').read()
    codecs.open(f'{COMPANY}_{YEAR}_cp437.se', 'w', encoding='cp437').write(nfo)
except:
  print("An exception while converting SIE4 to CP437")
