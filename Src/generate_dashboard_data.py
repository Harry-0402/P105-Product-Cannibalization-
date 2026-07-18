"""
Generate pre-aggregated data for the HTML dashboard.
Reads the cleaned CSV and outputs a JavaScript data file (data.js).
"""

import pandas as pd
import numpy as np
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'Data')
DASH_DIR = os.path.join(BASE, 'Dashboard')
os.makedirs(DASH_DIR, exist_ok=True)

LAUNCH_DATE = pd.Timestamp('2024-06-01')
LAUNCHED_PRODUCTS = ['P1', 'P2', 'P3', 'P4', 'P5']
AFFECTED_GROUPS = ['G1', 'G2']

print("Generating dashboard data...")

# ── Load Data ──
df = pd.read_csv(os.path.join(DATA_DIR, 'cannibalization_cleaned.csv'))
df['Date'] = pd.to_datetime(df['Date'])
before = df[df['Period_Flag'] == 'Before_Launch']
after  = df[df['Period_Flag'] == 'After_Launch']

data = {}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. KPI Cards
# ═══════════════════════════════════════════════════════════════════════════════

months_before = before['Year_Month'].nunique()
months_after  = after['Year_Month'].nunique()

p6_b = before[before['Product_ID'] == 'P6']['Sales'].sum()
p6_a = after[after['Product_ID'] == 'P6']['Sales'].sum()
p6_loss = (p6_b / months_before) * months_after - p6_a
p4p5_gain = after[after['Product_ID'].isin(['P4', 'P5'])]['Sales'].sum()
cann_rate = round((p6_loss / p4p5_gain * 100), 1) if p4p5_gain > 0 else 0

cust_before_set = set(before['Customer_ID'])
cust_after_set  = set(after['Customer_ID'])
cust_retained   = cust_before_set & cust_after_set
retention_rate  = round(len(cust_retained) / len(cust_before_set) * 100, 1)

cust_p6_before = set(before[before['Product_ID'] == 'P6']['Customer_ID'])
cust_new_after = set(after[after['Product_ID'].isin(['P4', 'P5'])]['Customer_ID'])
switchers = cust_p6_before & cust_new_after
switching_rate = round(len(switchers) / len(cust_p6_before) * 100, 1) if cust_p6_before else 0

data['kpis'] = {
    'total_sales':        int(df['Sales'].sum()),
    'total_revenue':      round(df['Revenue'].sum(), 0),
    'avg_price':          round(df['Price'].mean(), 2),
    'avg_rating':         round(df['Rating'].mean(), 2),
    'sales_growth':       round((after['Sales'].mean() - before['Sales'].mean()) / before['Sales'].mean() * 100, 2),
    'revenue_growth':     round((after['Revenue'].mean() - before['Revenue'].mean()) / before['Revenue'].mean() * 100, 2),
    'cann_rate':          cann_rate,
    'switching_rate':     switching_rate,
    'retention_rate':     retention_rate,
    'mkt_roi':            round(df['Revenue'].sum() / df['Marketing_Spend'].sum(), 2),
    'stock_avail':        round(df['Stock_Available'].mean() * 100, 1),
    'total_products':     int(df['Product_ID'].nunique()),
    'total_customers':    int(df['Customer_ID'].nunique()),
    'oos_records':        int((df['Stock_Available'] == 0).sum()),
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Monthly Trends
# ═══════════════════════════════════════════════════════════════════════════════

monthly = df.groupby('Year_Month').agg(
    sales=('Sales', 'sum'),
    revenue=('Revenue', 'sum'),
    avg_price=('Price', 'mean'),
    records=('Sales', 'count')
).reset_index()
monthly.columns = ['month', 'sales', 'revenue', 'avg_price', 'records']
monthly['month_dt'] = pd.to_datetime(monthly['month'])
monthly.sort_values('month_dt', inplace=True)

data['monthly_trends'] = {
    'months':   monthly['month'].tolist(),
    'sales':    monthly['sales'].tolist(),
    'revenue':  [round(x, 0) for x in monthly['revenue'].tolist()],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Product Performance
# ═══════════════════════════════════════════════════════════════════════════════

prod = df.groupby('Product_ID').agg(
    total_sales=('Sales', 'sum'),
    total_revenue=('Revenue', 'sum'),
    avg_sales=('Sales', 'mean'),
    avg_price=('Price', 'mean'),
    avg_rating=('Rating', 'mean'),
    category=('Category', 'first'),
    group=('Product_Group', 'first')
).round(2).reset_index()

prod_before = before.groupby('Product_ID')['Sales'].mean().rename('avg_before')
prod_after  = after.groupby('Product_ID')['Sales'].mean().rename('avg_after')
prod_growth = pd.concat([prod_before, prod_after], axis=1).fillna(0)
prod_growth['growth_pct'] = ((prod_growth['avg_after'] - prod_growth['avg_before']) / prod_growth['avg_before'].replace(0, np.nan) * 100).round(2).fillna(0)

prod = prod.merge(prod_growth[['avg_before', 'avg_after', 'growth_pct']], on='Product_ID', how='left')
prod['is_launched'] = prod['Product_ID'].isin(LAUNCHED_PRODUCTS)
prod.sort_values('total_revenue', ascending=False, inplace=True)

data['products'] = prod.to_dict(orient='records')

# ═══════════════════════════════════════════════════════════════════════════════
# 4. Category Comparison
# ═══════════════════════════════════════════════════════════════════════════════

cat_period = df.groupby(['Category', 'Period_Flag']).agg(
    avg_sales=('Sales', 'mean'),
    total_revenue=('Revenue', 'sum'),
).reset_index()

categories = sorted(df['Category'].unique())
cat_data = []
for c in categories:
    cb = cat_period[(cat_period['Category']==c) & (cat_period['Period_Flag']=='Before_Launch')]
    ca = cat_period[(cat_period['Category']==c) & (cat_period['Period_Flag']=='After_Launch')]
    cat_data.append({
        'category': c,
        'sales_before': round(cb['avg_sales'].values[0], 2) if len(cb) else 0,
        'sales_after':  round(ca['avg_sales'].values[0], 2) if len(ca) else 0,
        'rev_before':   round(cb['total_revenue'].values[0], 0) if len(cb) else 0,
        'rev_after':    round(ca['total_revenue'].values[0], 0) if len(ca) else 0,
    })
data['categories'] = cat_data

# ═══════════════════════════════════════════════════════════════════════════════
# 5. Cannibalization Data
# ═══════════════════════════════════════════════════════════════════════════════

# P6 vs P4/P5 monthly
cann_prods = ['P4', 'P5', 'P6']
cann_monthly = df[df['Product_ID'].isin(cann_prods)].groupby(['Year_Month', 'Product_ID'])['Sales'].sum().reset_index()
cann_monthly['month_dt'] = pd.to_datetime(cann_monthly['Year_Month'])
cann_monthly.sort_values('month_dt', inplace=True)

cann_data = {}
for pid in cann_prods:
    pdata = cann_monthly[cann_monthly['Product_ID']==pid]
    cann_data[pid] = {
        'months': pdata['Year_Month'].tolist(),
        'sales': pdata['Sales'].tolist()
    }

data['cannibalization'] = {
    'rate': cann_rate,
    'p6_loss': int(p6_loss),
    'p4p5_gain': int(p4p5_gain),
    'switching_rate': switching_rate,
    'switchers': len(switchers),
    'p6_customers_before': len(cust_p6_before),
    'timeline': cann_data
}

# Customer migration
stayed_with_p6 = len(cust_p6_before & set(after[after['Product_ID']=='P6']['Customer_ID']))
lost = len(cust_p6_before) - len(switchers) - stayed_with_p6
data['cannibalization']['migration'] = {
    'switched': len(switchers),
    'stayed': stayed_with_p6,
    'lost': max(0, lost)
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. Regional Data
# ═══════════════════════════════════════════════════════════════════════════════

region_data = df.groupby('Region').agg(
    total_sales=('Sales', 'sum'),
    total_revenue=('Revenue', 'sum'),
    avg_sales=('Sales', 'mean'),
    customers=('Customer_ID', 'nunique'),
    avg_rating=('Rating', 'mean')
).round(2).reset_index()
data['regions'] = region_data.to_dict(orient='records')

# Region before/after
reg_period = df.groupby(['Region', 'Period_Flag'])['Sales'].mean().unstack().round(2).reset_index()
reg_period.columns = ['region', 'after', 'before']
data['region_period'] = reg_period.to_dict(orient='records')

# ═══════════════════════════════════════════════════════════════════════════════
# 7. Marketing Data
# ═══════════════════════════════════════════════════════════════════════════════

mkt_by_product = df.groupby('Product_ID').apply(
    lambda x: round(x['Revenue'].sum() / x['Marketing_Spend'].sum(), 2) if x['Marketing_Spend'].sum() > 0 else 0
).reset_index()
mkt_by_product.columns = ['product', 'roi']
mkt_by_product['is_launched'] = mkt_by_product['product'].isin(LAUNCHED_PRODUCTS)
data['marketing'] = mkt_by_product.sort_values('roi', ascending=False).to_dict(orient='records')

# ═══════════════════════════════════════════════════════════════════════════════
# 8. Pricing Data
# ═══════════════════════════════════════════════════════════════════════════════

price_bands = df.groupby('Price_Band', observed=True).agg(
    avg_sales=('Sales', 'mean'),
    total_revenue=('Revenue', 'sum'),
    count=('Sales', 'count')
).round(2).reset_index()
price_bands.columns = ['band', 'avg_sales', 'total_revenue', 'count']
data['price_bands'] = price_bands.to_dict(orient='records')

# ═══════════════════════════════════════════════════════════════════════════════
# 9. Inventory Data
# ═══════════════════════════════════════════════════════════════════════════════

stock_monthly = df.groupby('Year_Month').agg(
    in_stock=('Stock_Available', 'sum'),
    total=('Stock_Available', 'count')
).reset_index()
stock_monthly['pct'] = (stock_monthly['in_stock'] / stock_monthly['total'] * 100).round(1)
stock_monthly['month_dt'] = pd.to_datetime(stock_monthly['Year_Month'])
stock_monthly.sort_values('month_dt', inplace=True)

data['inventory'] = {
    'months': stock_monthly['Year_Month'].tolist(),
    'stock_pct': stock_monthly['pct'].tolist()
}

oos_by_prod = df[df['Stock_Available']==0].groupby('Product_ID').size().sort_values(ascending=False).reset_index()
oos_by_prod.columns = ['product', 'oos_count']
data['inventory']['oos_by_product'] = oos_by_prod.to_dict(orient='records')

# ═══════════════════════════════════════════════════════════════════════════════
# 10. Product Group Sales Trends
# ═══════════════════════════════════════════════════════════════════════════════

grp_monthly = df.groupby(['Year_Month', 'Product_Group'])['Sales'].sum().reset_index()
grp_monthly['month_dt'] = pd.to_datetime(grp_monthly['Year_Month'])
grp_monthly.sort_values('month_dt', inplace=True)

grp_trends = {}
for grp in sorted(df['Product_Group'].unique()):
    gdf = grp_monthly[grp_monthly['Product_Group']==grp]
    grp_trends[grp] = {
        'months': gdf['Year_Month'].tolist(),
        'sales': gdf['Sales'].tolist()
    }
data['group_trends'] = grp_trends

# ═══════════════════════════════════════════════════════════════════════════════
# 11. Recommendations
# ═══════════════════════════════════════════════════════════════════════════════

data['recommendations'] = [
    {'area': 'Product Strategy', 'priority': 'High', 'impact': 'High',
     'text': 'Monitor P6 closely. Consider differentiating or phasing it out if decline continues. P4/P5 are cannibalizing its market share.'},
    {'area': 'Pricing Strategy', 'priority': 'High', 'impact': 'Medium',
     'text': 'Reposition P6 pricing to compete with P4/P5. Consider promotional pricing for P6 to retain existing customers.'},
    {'area': 'Marketing Focus', 'priority': 'Medium', 'impact': 'High',
     'text': 'Redirect marketing spend to support P6 retention while promoting P4/P5 to new customer segments.'},
    {'area': 'Inventory Planning', 'priority': 'Medium', 'impact': 'Medium',
     'text': 'Maintain strong stock availability. Stockouts compound cannibalization by pushing customers to alternatives.'},
    {'area': 'Customer Retention', 'priority': 'High', 'impact': 'High',
     'text': 'Implement loyalty programs for P6 customers. Target switchers with win-back campaigns.'},
    {'area': 'Launch Strategy', 'priority': 'Medium', 'impact': 'High',
     'text': 'For future launches, assess cannibalization risk BEFORE launch. Target new customer segments.'},
    {'area': 'Growth Assessment', 'priority': 'High', 'impact': 'High',
     'text': 'Measure NET new revenue (growth minus cannibalized revenue) for accurate business assessment.'},
    {'area': 'Regional Strategy', 'priority': 'Low', 'impact': 'Low',
     'text': 'Regional performance is balanced. Continue uniform distribution strategy.'}
]

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════

# Convert numpy types for JSON
def convert(obj):
    if isinstance(obj, (np.integer,)):       return int(obj)
    if isinstance(obj, (np.floating,)):      return float(obj)
    if isinstance(obj, (np.bool_,)):         return bool(obj)
    if isinstance(obj, np.ndarray):          return obj.tolist()
    if isinstance(obj, pd.Timestamp):        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

js_content = "// Auto-generated dashboard data\nconst DASHBOARD_DATA = " + json.dumps(data, default=convert, indent=2) + ";\n"

output_path = os.path.join(DASH_DIR, 'data.js')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Dashboard data saved to: {output_path}")
print(f"Data sections: {list(data.keys())}")
