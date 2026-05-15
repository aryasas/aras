import os
import sys

# Add api directory to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'api'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.base.model import Model
from core.logic.ui_generator import UIGenerator
# Import apps to trigger model registration
from apps.erp.stock import models as stock_models
from apps.erp.config import models as config_models
from apps.erp.accounting import models as accounting_models
from apps.erp.crm import models as crm_models
from apps.erp.pos import models as pos_models
from apps.erp.supplier import models as supplier_models

def main():
    engine = create_engine("sqlite:///api/aras.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # We want to check erp_stock_products
    product_model = None
    for mapper in Model.registry.mappers:
        if mapper.class_.__tablename__ == 'erp_stock_products':
            product_model = mapper.class_
            break
            
    if product_model:
        print("Model._child_map:")
        import json
        print(json.dumps(Model._child_map, indent=2))
        
        metadata = UIGenerator.generate_metadata(product_model, db=db)
        print("Children for erp_stock_products:")
        import json
        print(json.dumps(metadata.get('children', []), indent=2))
    else:
        print("Model erp_stock_products not found.")

if __name__ == '__main__':
    main()
