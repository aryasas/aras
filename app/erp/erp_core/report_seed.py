# Reports are stored in the erp_report table.
# Use ErpReport model to manage them; report_runner.py executes them.


def run_seed(app=None):
    print("[seed] reports managed via erp_report table — no hardcoded seed needed.")
