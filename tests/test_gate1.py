import numpy as np,pandas as pd,pytest
from studies.gate1 import metrics,strat_returns
def mpx(n=600,k=3,seed=0):
    rng=np.random.default_rng(seed); idx=pd.date_range("2018-01-01",periods=n,freq="B")
    return pd.DataFrame({f"T{i}":100*np.cumprod(1+rng.normal(.0003,.01,n)) for i in range(k)},index=idx)
_L=lambda c:pd.Series(1,index=c.index); _F=lambda c:pd.Series(0,index=c.index)
def test_pos(): m=metrics(pd.Series([.001]*300)); assert m["sharpe"]>0 and m["max_dd"]==0.0
def test_neg(): m=metrics(pd.Series([-.001]*300)); assert m["sharpe"]<0
def test_short(): assert metrics(pd.Series([.01]*10)) is None
def test_zero(): assert metrics(pd.Series([0.]*300)) is None
def test_hit(): assert abs(metrics(pd.Series([.01,-.01]*150))["hit"]-0.5)<0.01
def test_shape(): s,b=strat_returns(mpx(),_L); assert len(s)==len(b)==len(mpx())
def test_flat(): assert strat_returns(mpx(),_F)[0].abs().sum()<.01
def test_nolook(): assert strat_returns(mpx(k=1),_L)[0].iloc[0]==0.0
def test_short_empty(): assert strat_returns(mpx(n=100,k=2),_L)[0].empty
def test_nonzero(): s,b=strat_returns(mpx(seed=42),_L); assert (1+s).cumprod().iloc[-1]>0
