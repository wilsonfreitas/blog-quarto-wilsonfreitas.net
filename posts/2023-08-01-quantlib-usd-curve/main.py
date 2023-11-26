# %% [markdown]
# ---
# title: "QuantLib: Curva de Cupom Cambial"
# description: |
#     Como construir a curva de cupom cambial.
# author:
#   - name: Wilson Freitas
#     url: {}
# date: 2023-08-01
# categories:
#   - python
#   - quantlib
#   - brasa
# ---

# %%
import os

os.environ["BRASA_DATA_PATH"] = "D:\\brasa"
import brasa
import pyarrow.compute as pc
from datetime import datetime
import QuantLib as ql

import pandas as pd
import matplotlib.ticker as mticker

refdate = datetime(2023, 7, 14)
refdate_1 = datetime(2023, 7, 13)

fut_dol = (
    brasa.get_dataset("b3-futures-dol")
    .filter(pc.field("refdate") == refdate)
    .to_table()
    .to_pandas()
)

fut_di1 = (
    brasa.get_dataset("b3-futures-di1")
    .filter(pc.field("refdate") == refdate)
    .to_table()
    .to_pandas()
)

today = ql.Date().from_date(refdate)
ql.Settings.instance().evaluationDate = today
calendar = ql.Brazil(ql.Brazil.Settlement)

# %%
cdi = (
    brasa.get_dataset("b3-economic-indicators-price")
    .filter(pc.field("refdate") == refdate)
    .filter(pc.field("commodity") == "DI1")
    .filter(pc.field("symbol") == "RTDI1")
    .to_table(columns=["price"])
    .to_pandas()
    .iloc[0, 0]
) / 100

# %%
df_econ_ind = (
    brasa.get_dataset("b3-economic-indicators-price")
    .filter(
        pc.field("refdate") >= calendar.advance(today, ql.Period(-1, ql.Days)).to_date()
    )
    .filter(pc.field("refdate") <= refdate)
    .filter(pc.field("commodity") == "DOL")
    .to_table()
    .to_pandas()
)

# %%
df_econ_ind

# %%
fut = fut_dol.merge(
    fut_di1, on=["refdate", "maturity_date", "business_days"], suffixes=("_dol", "_di1")
)

# %%
from bizdays import Calendar, set_option

set_option("mode", "pandas")

cal_dc = Calendar(name="actual")
cal_du = Calendar.load("ANBIMA")

# %%
ptax_1 = df_econ_ind.loc[
    (df_econ_ind["refdate"] == refdate_1) & (df_econ_ind["symbol"] == "RTDOLT1"),
    "price",
].item()
di1_factor = 100000 / fut["settlement_price_di1"]
dol_factor = fut["settlement_price_dol"] / (ptax_1 * 1000)
fut["fixing"] = cal_du.offset(cal_du.following(fut["maturity_date"]), 1)
dc = cal_dc.bizdays(cal_du.offset(refdate, 1), fut["fixing"])
fut["cupom_sujo"] = (di1_factor / dol_factor - 1) * 360 / dc

# %%
spot = df_econ_ind.loc[
    (df_econ_ind["refdate"] == refdate) & (df_econ_ind["symbol"] == "RTDOLCL"), "price"
].item()
di1_factor = (100000 / fut["settlement_price_di1"]) / ((1 + cdi) ** (1 / 252))
dol_factor = fut["settlement_price_dol"] / (spot * 1000)
dc = cal_dc.bizdays(cal_du.offset(refdate, 2), fut["fixing"])
fut["cupom_limpo"] = (di1_factor / dol_factor - 1) * 360 / dc
fut["dc_limpo"] = dc

# %%
us_curve = pd.concat(
    [
        pd.Series([1, 2, 3, 4, 6, 12, 24, 36, 60, 72, 120, 240, 360]) * 30,
        pd.Series(
            [
                5.37,
                5.49,
                5.49,
                5.53,
                5.52,
                5.34,
                4.74,
                4.35,
                4.04,
                3.94,
                3.83,
                4.11,
                3.93,
            ]
        )
        / 100,
    ],
    axis=1,
)

us_curve.columns = ["dc", "rate"]

# %%
us_curve["date"] = cal_dc.offset(refdate, us_curve["dc"])

# %%
fut

# %%
ax = fut[["fixing", "cupom_limpo", "cupom_sujo"]].set_index("fixing").plot()
us_curve[["date", "rate"]].query("date <= '2027-01-01'").set_index("date").plot(ax=ax)

# %% [markdown]
# ### ZeroCurves
#
#

# %%
fut

# %%
data = [(ql.Date.from_date(d), r) for d, r in zip(fut["fixing"], fut["cupom_limpo"])]
data.insert(0, (today, data[0][1]))
dates, yields = zip(*data)

# %%
dates

# %%
fut

# %%
zc = ql.ZeroCurve(dates, yields, ql.Actual360())

# %%
zc.referenceDate()

# %%
zc.nodes()[:5]
