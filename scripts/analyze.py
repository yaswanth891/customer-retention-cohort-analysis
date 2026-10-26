"""Analyze Olist-style delivered orders, repeat purchase, and cohort retention."""
import argparse
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from dashboard_utils import dashboard
BASE=Path(__file__).resolve().parents[1]

def load_purchases(orders,customers):
    req_orders={'order_id','customer_id','order_status','order_purchase_timestamp'}
    req_customers={'customer_id','customer_unique_id'}
    if not req_orders.issubset(orders):raise ValueError('Missing orders fields: '+str(req_orders-set(orders)))
    if not req_customers.issubset(customers):raise ValueError('Missing customers fields: '+str(req_customers-set(customers)))
    o=orders.copy().drop_duplicates('order_id')
    c=customers.copy().drop_duplicates('customer_id')
    if 'customer_state' not in c:c['customer_state']='Unknown'
    o=o[o.order_status=='delivered'].copy()
    o['purchased_at']=pd.to_datetime(o['order_purchase_timestamp'],errors='coerce')
    o=o.dropna(subset=['purchased_at'])
    merged=o.merge(c[['customer_id','customer_unique_id','customer_state']],on='customer_id',how='inner',validate='many_to_one')
    merged=merged.dropna(subset=['customer_unique_id'])
    if merged.empty: raise ValueError('No matching delivered purchases found')
    merged['purchased_at']=merged.purchased_at.dt.strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(':memory:') as con:
        merged[['order_id','customer_unique_id','customer_state','purchased_at']].to_sql('delivered_orders',con,index=False,if_exists='replace')
        sql=(BASE/'sql/retention.sql').read_text()
        df=pd.read_sql_query(sql,con)
    for col in ['purchased_at','first_purchase_at']:
        df[col]=pd.to_datetime(df[col])
    return df

def cohort_table(purchases,max_age=5):
    d=purchases.copy()
    d['cohort_month']=d.first_purchase_at.dt.to_period('M')
    d['purchase_month']=d.purchased_at.dt.to_period('M')
    d['age']=(d.purchase_month.dt.year-d.cohort_month.dt.year)*12+(d.purchase_month.dt.month-d.cohort_month.dt.month)
    d=d[d.age>=0]
    last_month=d.purchase_month.max()  # conservatively mark this final observed month incomplete
    counts=d.groupby(['cohort_month','age']).customer_unique_id.nunique()
    sizes=d.groupby('cohort_month').customer_unique_id.nunique()
    records=[]
    for month,n in sizes.items():
        rec={'cohort_month':str(month),'cohort_size':int(n)}
        for age in range(max_age+1):
            eligible=month+age < last_month or (age==0)
            rec[f'month_{age}']= (float(counts.get((month,age),0)/n) if eligible else np.nan)
        records.append(rec)
    return pd.DataFrame(records).sort_values('cohort_month').reset_index(drop=True)

def repeat_30d(purchases):
    first=purchases[purchases.order_number==1].copy()
    max_observed=purchases.purchased_at.max()
    first=first[first.first_purchase_at<=max_observed-pd.Timedelta(days=30)].copy()
    later=purchases[purchases.order_number>1].copy()
    later=later.merge(first[['customer_unique_id','first_purchase_at']],on='customer_unique_id',how='inner',suffixes=('','_eligible'))
    later['days']=(later.purchased_at-later.first_purchase_at).dt.total_seconds()/86400
    repeat_ids=set(later.loc[later.days.between(0,30,inclusive='right'),'customer_unique_id'])
    first['repeat_30d']=first.customer_unique_id.isin(repeat_ids)
    return first

def run(orders_path=None, customers_path=None, output_dir=None):
    orders_path=Path(orders_path or BASE/'data/raw/olist_orders_dataset.csv')
    customers_path=Path(customers_path or BASE/'data/raw/olist_customers_dataset.csv')
    out=Path(output_dir or BASE/'outputs');out.mkdir(parents=True,exist_ok=True)
    p=load_purchases(pd.read_csv(orders_path),pd.read_csv(customers_path))
    cohorts=cohort_table(p)
    eligible=repeat_30d(p)
    repeat_rate=float(eligible.repeat_30d.mean()) if len(eligible) else 0
    monthly=p[p.order_number==1].groupby(p[p.order_number==1].first_purchase_at.dt.to_period('M')).size()
    state=eligible.groupby('customer_state').agg(eligible_customers=('customer_unique_id','size'),repeat_rate=('repeat_30d','mean'))
    state=state[state.eligible_customers>=50].sort_values('eligible_customers',ascending=False).head(8)
    metrics={'delivered_orders':len(p),'unique_buyers':int(p.customer_unique_id.nunique()),
             'eligible_30d_buyers':len(eligible),'repeat_30d_rate':repeat_rate,
             'first_month_retention_eligible_cohorts':int(cohorts.month_1.notna().sum()),
             'demo_data':bool(orders_path.resolve()==(BASE/'data/raw/olist_orders_dataset.csv').resolve()
                              and (BASE/'data/raw/DEMO_DATA.txt').exists())}
    cohorts.to_csv(out/'cohort_retention.csv',index=False)
    eligible[['customer_unique_id','customer_state','first_purchase_at','repeat_30d']].to_csv(out/'eligible_repeat_customers.csv',index=False)
    state.to_csv(out/'state_segments.csv')
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2))
    eligible_cohorts=cohorts.dropna(subset=['month_1']).tail(12).copy()
    if eligible_cohorts.empty:eligible_cohorts=cohorts.tail(12).copy()
    heat=eligible_cohorts[[f'month_{i}' for i in range(6)]].to_numpy(dtype=float)*100
    labels=[f'M{i}' for i in range(6)]
    fig1=go.Figure(go.Heatmap(z=heat,y=eligible_cohorts.cohort_month,x=labels,
           hovertemplate='Cohort %{y}<br>Age %{x}<br>Retention %{z:.1f}%<extra></extra>',
           colorscale=[[0,'#132741'],[.4,'#286a82'],[1,'#30d7bd']],zmin=0,zmax=100,
           text=np.where(np.isfinite(heat),np.round(heat,1).astype(str)+'%',''),texttemplate='%{text}'))
    fig1.update_xaxes(title='Months since first order')
    fig2=go.Figure(go.Bar(x=monthly.index.astype(str),y=monthly.values,marker_color='#64a9f8'))
    fig2.update_xaxes(title='First-purchase month');fig2.update_yaxes(title='New purchasers')
    fig3=go.Figure(go.Bar(x=state.index.astype(str),y=state.repeat_rate*100,marker_color='#36d6bd',
                            customdata=state.eligible_customers,hovertemplate='%{x}: %{y:.1f}% repeat<br>Eligible: %{customdata}<extra></extra>'))
    fig3.update_yaxes(title='Repeat in 30 days (%)',rangemode='tozero')
    finding=('30-day repeat purchase measures a second completed order within 30 days after the first purchase. '
             'Build a post-purchase re-engagement hypothesis for cohorts with weaker repeat behavior, '
             'then evaluate it with a randomized campaign before claiming any improvement.')
    footnote=('DATA: SYNTHETIC DEMO — NOT REAL BUSINESS RESULTS. ' if metrics['demo_data'] else 'DATA: USER-SUPPLIED DATASET. ')+(
         'Only delivered orders count; persistent customer_unique_id links orders. Month 0 is 100% by definition. '
         'The latest observed calendar month is treated as incomplete; 30-day repeat excludes buyers lacking 30 days of follow-up. '
         'Retention is descriptive, not causal.')
    dashboard(out/'dashboard.html','Customer Retention & Cohort Analysis',
          'Track whether first-time buyers return, while handling incomplete follow-up periods.',
          [('Delivered orders',f'{len(p):,}'),('Unique buyers',f"{metrics['unique_buyers']:,}"),
           ('30-day-eligible buyers',f'{len(eligible):,}'),('Repeat within 30 days',f'{repeat_rate:.1%}')],
          [('Monthly cohort retention',fig1),('New buyers by month',fig2),('Repeat rate by state',fig3)],finding,footnote)
    fig,ax=plt.subplots(figsize=(10,5.7));fig.patch.set_facecolor('#0b1324');ax.set_facecolor('#17223a')
    im=ax.imshow(heat,cmap='YlGnBu',vmin=0,vmax=100,aspect='auto')
    ax.set_xticks(range(6),labels);ax.set_yticks(range(len(eligible_cohorts)),eligible_cohorts.cohort_month)
    ax.tick_params(colors='white');ax.set_title('MONTHLY CUSTOMER RETENTION (COHORT HEATMAP)',color='white',weight='bold',pad=16)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            if np.isfinite(heat[i,j]):ax.text(j,i,f'{heat[i,j]:.1f}%',ha='center',va='center',fontsize=8,color='white' if heat[i,j]>52 else '#17223a')
    fig.tight_layout();fig.savefig(out/'overview.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    (out/'insights.md').write_text(f'''# Product insight memo — Customer Retention

**Dataset:** {'Synthetic demonstration data (not actual shoppers)' if metrics['demo_data'] else orders_path.name+' and '+customers_path.name}

**Business question:** What share of customers make another purchase, and which first-purchase cohorts stay active?

## Metrics and findings

- **{len(p):,}** delivered orders from **{metrics['unique_buyers']:,}** distinct buyers (`customer_unique_id`).
- **{len(eligible):,}** buyers are eligible for a fully observed 30-day repeat window.
- **{repeat_rate:.2%}** of eligible buyers placed another delivered order within 30 days.
- Cohort heatmap is **the fraction of cohort customers who purchase in calendar month M1..M5**, not a survival curve. Month 0 is 100%.

## Product recommendations

1. Investigate the timing and customer segment of return purchases, without confusing correlation with causal impact.
2. Prototype a post-purchase retention email or discount experiment; measure 30-day repeat purchase against a control group.
3. Segment by geography only when sample sizes support it; do not assume the causes of differences.

## Limitations

Exclude orders not marked delivered. Last observed month is treated as incomplete for cohort cells. 30-day repeat is measured only for fully eligible users. No order-item prices are used, so **this project does not estimate customer lifetime value (LTV)**. No uplift claims are made. Synthetic demo results are not real business evidence.
''')
    print(f"Retention: {len(p):,} delivered orders, {metrics['unique_buyers']:,} buyers, repeat-30d {repeat_rate:.2%}. Dashboard: {out/'dashboard.html'}")
    return metrics

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--orders');ap.add_argument('--customers');ap.add_argument('--out')
    a=ap.parse_args();run(a.orders,a.customers,a.out)
