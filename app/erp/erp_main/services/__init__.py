# DocSeries supersedes the old `sequence` service. Keep `sequence` as an
# alias so existing call sites (`from app.erp.erp_main.services import sequence as seq_svc`)
# keep working without churn.
from . import doc_series as sequence  # noqa: F401
