print(1)

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

cdi = (
    brasa.get_dataset("b3-economic-indicators-price")
    .filter(pc.field("refdate") == refdate)
    .filter(pc.field("commodity") == "DI1")
    .filter(pc.field("symbol") == "RTDI1")
    .to_table(columns=["price"])
    .to_pandas()
    .iloc[0, 0]
) / 100

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
