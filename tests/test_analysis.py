import unittest
import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from analyze import load_purchases,cohort_table,repeat_30d

class TestRetention(unittest.TestCase):
    def setUp(self):
        self.orders=pd.DataFrame([
            ('o1','c1','delivered','2025-01-01 10:00:00'),
            ('o2','c2','delivered','2025-01-20 10:00:00'),
            ('o3','c3','delivered','2025-02-10 10:00:00'),
            ('o4','c4','canceled','2025-02-15 10:00:00'),
            ('o5','c5','delivered','2025-03-20 10:00:00'),
        ],columns=['order_id','customer_id','order_status','order_purchase_timestamp'])
        self.customers=pd.DataFrame([('c1','a'),('c2','a'),('c3','b'),('c4','a'),('c5','c')],columns=['customer_id','customer_unique_id'])
    def test_filters_canceled_and_joins_unique_buyer(self):
        p=load_purchases(self.orders,self.customers)
        self.assertEqual(len(p),4);self.assertEqual(p.customer_unique_id.nunique(),3)
    def test_cohort_month0(self):
        p=load_purchases(self.orders,self.customers)
        c=cohort_table(p,max_age=2)
        self.assertTrue((c.month_0==1).all())
        self.assertAlmostEqual(float(c.loc[c.cohort_month=='2025-01','month_1'].iloc[0]),0)
    def test_repeat_window(self):
        p=load_purchases(self.orders,self.customers)
        x=repeat_30d(p)
        self.assertEqual(len(x),2)  # Jan 1 and Feb 10 eligible by March 20
        self.assertEqual(int(x.repeat_30d.sum()),1)
    def test_missing_schema(self):
        with self.assertRaises(ValueError):load_purchases(pd.DataFrame({'x':[1]}),self.customers)

if __name__=='__main__':unittest.main()
