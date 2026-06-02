import numpy as np,pandas as pd,pytest
from studies.gate0 import ic,conditional,incremental,permutation,sma_state
def mf(n=500,seed=0):
    rng=np.random.default_rng(seed); sig=pd.Series(rng.choice([-1,0,1],size=n))
    return pd.DataFrame({"sig":sig,"fwd":pd.Series(sig*0.01+rng.normal(0,.005,n))})
def mn(n=500,seed=1):
    rng=np.random.default_rng(seed); sig=pd.Series(rng.choice([-1,0,1],size=n))
    return pd.DataFrame({"sig":sig,"fwd":pd.Series(rng.normal(0,.01,n))})
def test_ic_pos(): assert ic(mf()["sig"],mf()["fwd"])>0.30
def test_ic_noise(): assert abs(ic(mn()["sig"],mn()["fwd"]))<0.15
def test_ic_few(): assert ic(pd.Series([1,-1,1]),pd.Series([.01,-.01,.01]))==0.0
def test_ic_const(): assert ic(pd.Series([1]*200),pd.Series(np.random.randn(200)))==0.0
def test_mono(): assert conditional(mf(n=2000))[3]
def test_mono_bool(): assert isinstance(conditional(mn(n=2000,seed=99))[3],bool)
def test_inc_no_base(): feat=mf(); s,_,best,edge=incremental(feat,[]); assert best==0.0 and edge==s
def test_inc_nonneg():
    rng=np.random.default_rng(7); n=600; sig=pd.Series(rng.choice([-1,0,1],size=n))
    feat=pd.DataFrame({"sig":sig,"fwd":pd.Series(sig*0.01+rng.normal(0,.005,n)),"rand":pd.Series(rng.choice([-1,0,1],size=n))})
    assert incremental(feat,["rand"])[0]>=0
def test_perm_strong(): assert permutation(mf(n=1000),n=200)[2]>80
def test_perm_noise(): assert permutation(mn(n=1000),n=200)[2]<80
def test_sma_above(): assert sma_state(pd.Series([100.]*210+[110.]*10),200).iloc[-1]==1
def test_sma_below(): assert sma_state(pd.Series([100.]*210+[90.]*10),200).iloc[-1]==-1
