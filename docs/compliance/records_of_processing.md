# Records of Processing Activities (ROPA) — GDPR Art. 30

This document tracks personal data processing activities within Aras.

## Data Categories & Fields
Fields tagged with `pii=True` in the model metadata:

| Model | Table | PII Fields | Purpose | Legal Basis | Retention | Recipient |
|-------|-------|------------|---------|-------------|-----------|-----------|
| User | `core_users` | `name`, `email` | Authentication, Profile | Contractual | Indefinite | Internal |
| Subscription | `saas_subscription` | `email`, `company_name`, `full_name`, `phone` | Tenancy, Billing | Contractual | 7 years | Stripe/Midtrans/Xendit |
| Party | `party_parties` | `name`, `email`, `phone` | CRM, Transactions | Contractual | TODO | Internal |
| Organization | `core_organizations` | `legal_name`, `trade_name`, `tax_id`, `address`, `phone`, `email` | Identity, Tax | Legal Obligation | TODO | Tax Authorities |

## Processing Purposes
- **Authentication**: Managing user accounts and security.
- **Tenancy**: Providing isolated environments for customers.
- **Billing**: Processing payments for SaaS plans.
- **CRM & Transactions**: Managing customer/supplier relations and business documents.
- **Identity & Tax**: Recording legal entity details for compliance.

## Recipients & Third Parties
- **Stripe**: Payment processing (PCI-DSS compliant).
- **Midtrans**: Payment processing (Indonesia).
- **Xendit**: Payment processing (SEA).
- **Postmark/Resend**: Transactional emails.

## Retention & Erasure
- **Retention**: Configured via `retention_days` on log models. Master data retention varies by jurisdiction (TODO).
- **Erasure**: User deletion triggers anonymization (`anonymize_self`), which replaces PII with tombstones instead of cascading deletion.

## Security Measures
- Encryption at rest (DB).
- TLS 1.3 for data in transit.
- Bcrypt for password hashing.
- SHA256 for refresh token hashing.
- CSP nonces and secure security headers.
- Automatic PII redaction in audit logs.
