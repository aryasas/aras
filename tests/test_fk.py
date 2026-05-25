import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'api'))

from apps.stock import models

def test():
    for col in models.PriceList.__table__.columns:
        for fk in col.foreign_keys:
            try:
                target_table = getattr(fk, "_column_tokens", [None])[1] if hasattr(fk, "_column_tokens") else fk.target_fullname.split('.')[0]
                print(f"Col {col.name} -> {target_table}")
                # let's also try accessing fk.column
                print(f"  fk.target_fullname: {fk.target_fullname}")
            except Exception as e:
                print(f"Error on col {col.name}: {e}")

test()
