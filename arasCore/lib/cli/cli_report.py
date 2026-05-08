import click

def register_report_commands(aras):
    @aras.command("check-reports", help="Check all ERP reports for SQL or script errors")
    @click.option("--id", "report_id", type=int, help="Check specific report ID")
    @click.option("--company-id", type=int, default=1, help="Company ID for context")
    def check_reports(report_id, company_id):
        import flask
        _app = flask.current_app._get_current_object()
        with _app.app_context():
            try:
                from app.erp.erp_main.models.report import ErpReport
                from app.erp.erp_main.services.report_runner import run_report
            except ImportError:
                click.echo("erp not installed or erp_core models not found.")
                return

            if report_id:
                report = ErpReport.query.get(report_id)
                if not report:
                    click.echo(f"Report ID {report_id} not found.")
                    return
                reports = [report]
            else:
                reports = ErpReport.query.all()

            if not reports:
                click.echo("No reports found to check.")
                return

            passed = 0
            failed = 0
            
            click.echo(f"Checking {len(reports)} report(s)...")
            for r in reports:
                click.echo(f"  [{r.id}] {r.title} ({r.report_type})... ", nl=False)
                res = run_report(r.id, {}, company_id=company_id)
                
                if res.get("error"):
                    click.echo(click.style("FAILED", fg="red"))
                    click.echo(click.style("-" * 40, fg="bright_black"))
                    click.echo(click.style(f"{res['error']}", fg="yellow"))
                    click.echo(click.style("-" * 40, fg="bright_black"))
                    failed += 1
                else:
                    click.echo(click.style("OK", fg="green"))
                    passed += 1
            
            click.echo(f"\nSummary: {passed} passed, {failed} failed.")
