#!/usr/bin/env python3
#
# Playground for GnuCash reports on top of sqlite db
#
# SIE4-export assumes that verification with num 1 has initial balances
#
# Resources
# * https://wiki.gnucash.org/wiki/SQL
# * https://sietest.sie.se/

import sqlite3
import argparse
import pandas as pd
import sys
import codecs
import datetime as dt

from pathlib import Path
from os.path import exists


# DB_PATH = '../sqlitedb'
DB_EXT  = 'gnucash'

EXCLUDE_TRANS = []
MOMS_KONTON = [1650, 2611, 2612, 2614, 2641, 2645, 2650]

PREVIOUS_FINANCIAL_YEAR_START = '20220511'
PREVIOUS_FINANCIAL_YEAR_END = '20221231'
FINANCIAL_YEAR_START = '20230101'
FINANCIAL_YEAR_END = '20231231'

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
def run_sql(sql):
    con = sqlite3.connect(DB_FILE)
    df = pd.read_sql(sql, con)
    con.close()
    return df


df = run_sql(
    'select'
    '   t.post_date, t.enter_date, t.description,'
    '   s.tx_guid, s.memo, s.value_num, s.quantity_denom,'
    '   a.name, a.account_type, a.code,'
    '   i.id invoice_id,'
    '   c.id customer_id, c.name customer_name,'
    '   v.id vendor_id, v.name vendor_name'
    ' from transactions t'
    '   left join splits s'
    '     on s.tx_guid=t.guid'
    '   left join accounts a'
    '     on a.guid=s.account_guid'
    '   left join invoices i'
    '     on i.post_txn=t.guid or i.post_lot=s.lot_guid or i.id=t.num'
    '   left join customers c'
    '     on c.guid=i.owner_guid'
    '   left join vendors v'
    '     on v.guid=i.owner_guid'
    ' order by post_date')
grouped = df.groupby(['tx_guid'])


# Saw new-line in description once...
df = df.replace('\n','', regex=True)

#df['num'] = pd.to_numeric(df['num'])
df['code'] = pd.to_numeric(df['code'])

print('\nDropping rows without account code\n', df[df['code'].isnull()])
df = df[df['code'].notnull()]

#print('\nDropping rows without number \n', df[df['num'].isnull()])
#df = df[df['num'].notnull()]

df['post_date'] = pd.to_datetime(df['post_date'])
df['post_date'] = df['post_date'].dt.strftime('%Y%m%d')
print('\nDropping rows with post_date > FINANCIAL_YEAR_END\n')
df = df.loc[df['post_date'] <= FINANCIAL_YEAR_END]

df['code'] = df['code'].astype(int)
#df['num'] = df['num'].astype(int)
#df['invoice_id'] = df['invoice_id'].fillna('')
#df['customer_id'] = df['customer_id'].fillna('')
#df['vendor_id'] = df['vendor_id'].fillna('')

#df = df[~df['num'].isin(EXCLUDE_TRANS)]
df['value'] = df['value_num'] / df['quantity_denom']
df = df.drop(columns=['value_num', 'quantity_denom'])
df.to_csv(f'{COMPANY}_{YEAR}.csv', index=False)


print('\n************************** Accounts ***********************************')
dfa = df[['code', 'name']].sort_values('code').drop_duplicates('code')

account_codes = dfa['code'].to_list()
accounts = ''
for index, row in dfa.iterrows():
    accounts += '#KONTO {} \"{}\"\n'.format(
        row['code'],
        row['name'])

print(dfa.columns)
print(dfa.head(100))


print('\n************************** Balanskonton ***********************************')
dft = df[['post_date', 'code', 'value']]
dft = dft.loc[dft['code'] < 3000]

ib = ''
for year_code in [0, -1]:
    balance_start_date = FINANCIAL_YEAR_START if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_START

    dfb = dft.loc[dft['post_date'] < balance_start_date]
    dfb = (dfb[['code', 'value']]
        .groupby(['code'])
        .sum()
        .reset_index())

    # SIE4:
    # #IB 0 1311 100000
    # #IB -1 1311 90000
    for account_code in account_codes:
        row = dfb.loc[dfb['code'] == account_code]
        value = 0.0 if row.empty else row['value'].iloc[0]
        ib += '#IB {} {} {:.2f}\n'.format(
            year_code,
            account_code,
            value)

ub = ''
for year_code in [0, -1]:
    print('year_code=', year_code)
    balance_end_date = FINANCIAL_YEAR_END if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_END

    dfb = dft.loc[dft['post_date'] <= balance_end_date]
    dfb = (dfb[['code', 'value']]
        .groupby(['code'])
        .sum()
        .reset_index())

    # SIE4:
    # #UB 0 1311 100000
    # #UB -1 1311 90000
    for account_code in account_codes:
        row = dfb.loc[dfb['code'] == account_code]
        value = 0.0 if row.empty else row['value'].iloc[0]
        ub += '#UB {} {} {:.2f}\n'.format(
            year_code,
            account_code,
            value)

    print(dfb.columns)
    print(dfb.head(100))
    year = FINANCIAL_YEAR_END[:4] if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_END[:4]
    dfb.to_csv(f'{COMPANY}_{year}-balans.csv', index=False)

    ek = dfb[dfb["code"] < 2000].sum()[1]
    tillg = dfb[(dfb["code"] >= 2000) & (dfb["code"] < 3000)].sum()[1]
    print(f'EK:\t\t\t{ek:,.2f}')
    print(f'Tillgångar:\t\t{tillg:,.2f}')
    print(f'Beräknat resultat:\t{ek+tillg:,.2f}')
    print(f'')



print('\n************************** Resultatkonton ***********************************')
dft = df[['post_date', 'code', 'value']]
dft = dft.loc[dft['code'] >= 3000]

res_ = ''
for year_code in [0, -1]:
    print('year_code=', year_code)
    balance_start_date = FINANCIAL_YEAR_START if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_START
    balance_end_date = FINANCIAL_YEAR_END if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_END
    mask = (
        (dft['post_date'] >= balance_start_date)
        & (dft['post_date'] <= balance_end_date))
    dfr = (dft[['code', 'value']]
        .loc[mask]
        .groupby(['code'])
        .sum()
        .reset_index())

    # SIE:
    # #RES 0 3010 -400000
    # #RES -1 3010 -400000
    for account_code in account_codes:
        row = dfr.loc[dfr['code'] == account_code]
        value = 0.0 if row.empty else row['value'].iloc[0]
        res_ += '#RES {} {} {:.2f}\n'.format(
            year_code,
            account_code,
            value)

    print(dfr.columns)
    print(dfr.head(100))
    year = FINANCIAL_YEAR_END[:4] if year_code == 0 else PREVIOUS_FINANCIAL_YEAR_END[:4]
    dfr.to_csv(f'{COMPANY}_{year}-resultat.csv', index=False)
    print(f'Beräknat resultat:{dfr["value"].sum():,.2f} (<0 innebär vinst)')
    print(f'')



print('\n************************** MOMS-konton ***********************************')
dfM = df.loc[df['code'].isin(MOMS_KONTON)].reset_index()
dfM.loc[:, 'month'] = pd.to_datetime(dfM['post_date'])
grouped  = (dfM[['month', 'code', 'value']]
    .groupby(['code', pd.Grouper(key='month', freq='M')]))

dft = grouped.agg([
    ('Debit' , lambda x : x[x > 0].sum()),
    ('Kredit' , lambda x : x[x < 0].sum())])
print(dft)
dft.reset_index().to_csv(f'{COMPANY}_{YEAR}-moms.csv', index=False)

print('\n\n--- Totaler ---')
dft = grouped.sum()
print(dft)
dft.reset_index().to_csv(f'{COMPANY}_{YEAR}-moms-total.csv', index=False)




print('\n************************** SIE (alpha - experiment) ***********************************')

print('\nDropping rows with post_date < FINANCIAL_YEAR_START\n')
df = df.loc[df['post_date'] >= FINANCIAL_YEAR_START]

dim = '#DIM 8 Kund\n'
dim += '#DIM 9 Leverantör\n'
dim += '#DIM 10 Faktura\n'

invoices = (df[['invoice_id', 'customer_id', 'vendor_id']]
    .dropna(subset=['invoice_id'])
    .sort_values('invoice_id')
    .drop_duplicates())
customer_invoices = invoices.loc[invoices['customer_id'].notnull()]
print('customer invoices:', customer_invoices)
vendor_bills = invoices.loc[invoices['vendor_id'].notnull()]
print('vendor bills:', vendor_bills)

customers = (df[['customer_id', 'customer_name']]
    .dropna()
    .sort_values('customer_id')
    .drop_duplicates())
vendors = (df[['vendor_id', 'vendor_name']]
    .dropna()
    .sort_values('vendor_id')
    .drop_duplicates())

objects = ''
for _index, c in customers.iterrows():
    objects += '#OBJEKT 8 \"{}\" \"Kund: {}\"\n'.format(
        c['customer_id'], c['customer_name'])
for _index, v in vendors.iterrows():
    objects += '#OBJEKT 9 \"{}\" \"Leverantör: {}\"\n'.format(
        v['vendor_id'], v['vendor_name'])
for _index, i in customer_invoices.iterrows():
    objects += '#OBJEKT 10 \"{}\" \"Kundfaktura: #{}\"\n'.format(
        i['invoice_id'], i['invoice_id'])
for _index, i in vendor_bills.iterrows():
    objects += '#OBJEKT 10 \"{}\" \"Leverantörsfaktura: #{}\"\n'.format(
        i['invoice_id'], i['invoice_id'])

df = df.sort_values(['post_date', 'description', 'tx_guid', 'code'])
grouped = df.groupby(['post_date', 'description', 'tx_guid'])

prev_num = -1
res = ''
for idx, (tx_guid, tx_df) in enumerate(grouped):
    first_trans = True
    trans_balance = 0
    for index, row in tx_df.iterrows():
        if first_trans:
            first_trans = False
            res += '#VER A {} {} \"{}\"\n{{\n'.format(
                idx+1,
                row['post_date'][0:8],
                row['description'])
        customer_obj = '\"8\" \"{}\"'.format(row['customer_id']) if row['customer_id'] else ''
        vendor_obj = '\"9\" \"{}\"'.format(row['vendor_id']) if row['vendor_id'] else ''
        invoice_obj = '\"10\" \"{}\"'.format(row['invoice_id']) if row['invoice_id'] else ''
        objs = ''
        if customer_obj:
            if objs:
                objs += ' '
            objs += customer_obj
        if vendor_obj:
            if objs:
                objs += ' '
            objs += vendor_obj
        if invoice_obj:
            if objs:
                objs += ' '
            objs += invoice_obj
        res += '#TRANS {} {{{}}} {:.2f} \"\" \"{}\"\n'.format(
            row['code'],
            objs,
            row['value'],
            row['memo'])
        trans_balance += row['value']
    res += '}\n'
    if abs(trans_balance) > 0.001:
        print("Imbalanced transaction: #{} balance={}".format(idx+1, trans_balance))


# Add SIE header to file
header = Path(f'{COMPANY}_header.se').read_text()
print('\nAdding SIE header to SIE file\n', header)

res = (header + '\n'
    + accounts + '\n'
    + ib + '\n'
    + ub + '\n'
    + res_ + '\n'
    + dim + '\n'
    + objects + '\n'
    + res)

filename = f'{COMPANY}_{YEAR}.se'
file = open(filename, 'w')
file.write(res)
file.close()

try:
    nfo = codecs.open(filename, encoding='utf-8').read()
    codecs.open(f'{COMPANY}_{YEAR}_cp437.se', 'w', encoding='cp437').write(nfo)
except:
  print("An exception while converting SIE4 to CP437")
