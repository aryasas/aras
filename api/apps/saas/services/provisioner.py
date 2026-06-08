# gemini-2-5-flash
import logging
import secrets
import os
from core import Aras
from core.auth.service import create_access_token
from core.lib.helpers import slugify
from core.tenant.provisioner import provision_tenant as core_provision_tenant, seed_tenant
from datetime import datetime, timedelta

class Provisioner(Aras):
    @classmethod
    def provision_tenant(cls, db, subscription, region: str = None):
        """
        Full flow:
        1. Core provision (DB + migrations + registry)
        2. Seed (basic data)
        3. Issue license
        4. Return setup context
        """
        slug = slugify(subscription.company_name)
        tenant_id = f"{slug}-{subscription.id}"
        db_name = f"tenant_{subscription.id}_{slug.replace('-', '_')}"
        
        logging.info(f"Provisioning tenant for sub {subscription.id}: {tenant_id} (region: {region})")
        
        try:
            # 1. Create DB and run migrations
            core_provision_tenant(tenant_id, db_name, region=region)
            
            # 2. Seed basic data
            seed_tenant(tenant_id)
            
            # 3. Issue license
            from ..services.license_service import LicenseService
            license_token = LicenseService.issue_license(db, subscription.id, expiry_days=30)
            
            # 4. Generate setup link
            setup_token = create_access_token(
                {"sub": subscription.email, "purpose": "portal_setup", "tenant": tenant_id},
                expires_delta=timedelta(hours=24),
            )
            
            return {
                "tenant_id": tenant_id,
                "admin_email": subscription.email,
                "setup_token": setup_token,
                "license_token": license_token
            }
        except Exception as e:
            logging.error(f"Provisioning failed for {tenant_id}: {e}")
            raise
