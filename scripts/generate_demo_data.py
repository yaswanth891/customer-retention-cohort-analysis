"""Generate deterministic SYNTHETIC data with the Olist orders/customers schema."""
from pathlib import Path
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parents[1]

def generate(n_customers=15000,seed=43):
    rng=np.random.default_rng(seed)
    states=np.array(['SP','RJ','MG','RS','PR','SC','BA','PE','DF'])
    customers=[];orders=[];order_no=0
    start=pd.Timestamp('2024-01-01')
    for unique_id in range(n_customers):
        first=start+pd.Timedelta(days=int(rng.integers(0,650)))+pd.Timedelta(minutes=int(rng.integers(0,1440)))
        state=str(rng.choice(states,p=[.37,.16,.15,.09,.07,.06,.05,.03,.02]))
        dates=[first]
        if rng.random()<.29:
            dates.append(first+pd.Timedelta(days=int(rng.integers(2,150))))
        if rng.random()<.07:
            dates.append(dates[-1]+pd.Timedelta(days=int(rng.integers(5,120))))
        for d in dates:
            if d>pd.Timestamp('2025-12-31 23:59:59'): continue
            order_no+=1
            cid=f'cust_{order_no:07d}'
            status=str(rng.choice(['delivered','canceled','shipped'],p=[.96,.025,.015]))
            customers.append((cid,f'unique_{unique_id:07d}',12345,'demo_city',state))
            orders.append((f'order_{order_no:07d}',cid,status,d.strftime('%Y-%m-%d %H:%M:%S'),'', '', '', ''))
    return (pd.DataFrame(orders,columns=['order_id','customer_id','order_status','order_purchase_timestamp',
              'order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date']),
            pd.DataFrame(customers,columns=['customer_id','customer_unique_id','customer_zip_code_prefix','customer_city','customer_state']))

if __name__=='__main__':
    orders,customers=generate()
    orders.to_csv(BASE/'data/raw/olist_orders_dataset.csv',index=False)
    customers.to_csv(BASE/'data/raw/olist_customers_dataset.csv',index=False)
    print(f'SYNTHETIC sample: {len(orders):,} orders, {len(customers):,} order-linked customer IDs')
