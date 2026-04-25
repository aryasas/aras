import click

def _make_test_client_with_admin(flask_app):
    from arasCore.auth import User
    client = flask_app.test_client()
    with flask_app.app_context():
        user = User.query.filter_by(is_admin=True).first()
    if not user:
        return client, False
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return client, True

def register_test_commands(aras):
    @aras.group("test", help="Run automated tests against the running app")
    def test_group():
        pass

    @test_group.command("api", help="Test all registered API endpoints")
    @click.option("--verbose", "-v", is_flag=True, default=False)
    @click.option("--only-errors", "-e", is_flag=True, default=False)
    def test_api(verbose, only_errors):
        import flask
        _app = flask.current_app._get_current_object()
        _app.config["TESTING"] = True
        with _app.app_context():
            from arasCore.lib.api_handler import _api_registry
            client, ok = _make_test_client_with_admin(_app)
            if not ok: click.echo("[test api] WARNING: no admin user found")

            passed, failed = 0, []
            for key in sorted(_api_registry.keys()):
                url = f"/api/{key}/"
                resp = client.get(url)
                if resp.status_code in (200, 403):
                    passed += 1
                    if verbose and not only_errors: click.echo(f"  PASS {resp.status_code}  {url}")
                else:
                    failed.append((url, resp.status_code))
                    click.echo(f"  FAIL {resp.status_code}  {url}")

            click.echo(f"\n[test api] {passed} passed, {len(failed)} failed")
            if failed: raise SystemExit(1)

    @test_group.command("url", help="Test all non-parameterized GET routes")
    @click.option("--verbose", "-v", is_flag=True, default=False)
    @click.option("--only-errors", "-e", is_flag=True, default=False)
    def test_url(verbose, only_errors):
        import flask
        _app = flask.current_app._get_current_object()
        _app.config["TESTING"] = True
        with _app.app_context():
            client, ok = _make_test_client_with_admin(_app)
            if not ok: click.echo("[test url] WARNING: no admin user found")

            skip_prefixes = ("/static/", "/_debug_toolbar/")
            rules = sorted(
                (r for r in _app.url_map.iter_rules()
                if "GET" in r.methods
                and "<" not in r.rule
                and not any(r.rule.startswith(p) for p in skip_prefixes)),
                key=lambda r: r.rule,
            )

            passed, failed = 0, []
            for rule in rules:
                url = rule.rule
                resp = client.get(url)
                if resp.status_code in (200, 302, 403, 404, 405):
                    passed += 1
                    if verbose and not only_errors: click.echo(f"  PASS {resp.status_code}  {url}")
                else:
                    failed.append((url, resp.status_code))
                    click.echo(f"  FAIL {resp.status_code}  {url}")

            click.echo(f"\n[test url] {passed} passed, {len(failed)} failed")
            if failed: raise SystemExit(1)

    @test_group.command("errors", help="Run url+api tests and print grouped root-causes")
    def test_errors():
        import flask
        _app = flask.current_app._get_current_object()
        _prev_debug = _app.config.get("DEBUG", False)
        _app.config["TESTING"] = True
        _app.config["DEBUG"] = True
        try:
            _run_test_errors(_app)
        finally:
            _app.config["DEBUG"] = _prev_debug

def _run_test_errors(_app):
    import re, json as _json, traceback as _tb, click
    
    with _app.app_context():
        from arasCore.lib.api_handler import _api_registry
        client, ok = _make_test_client_with_admin(_app)

        def _is_auth_redirect(resp) -> bool:
            return resp.status_code in (301, 302) and ("login" in resp.headers.get("Location", "") or "/auth" in resp.headers.get("Location", ""))

        def _parse_tb(tb: str) -> tuple[str, str]:
            lines = tb.splitlines()
            exc_line = next((l.strip() for l in reversed(lines) if l.strip()), "")
            file_re = re.compile(r'\s*File "([^"]+)", line (\d+)(?:, in (.+))?')
            frames = []
            for i, l in enumerate(lines):
                m = file_re.match(l)
                if m:
                    path, ln, fn = m.group(1), m.group(2), m.group(3) or ""
                    code = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    for root in ("templates/", "arasCore/", "aras/"):
                        if root in path: path = path[path.index(root):]; break
                    frames.append((path, ln, fn, code))
            tmpl_frames = [f for f in frames if f[0].startswith("templates/")]
            proj_frames = [f for f in frames if f[0].startswith(("arasCore/", "aras/"))]
            chosen = (tmpl_frames or proj_frames or frames or [None])[-1]
            if chosen:
                path, ln, fn, code = chosen
                return exc_line, f"{path}:{ln}  {code[:100]}"
            return exc_line, ""

        def _capture(src: str, url: str, ok_codes: tuple):
            try:
                resp = client.get(url)
            except Exception: return (src, url, "EXC", _tb.format_exc().strip())
            if resp.status_code in ok_codes or _is_auth_redirect(resp): return None
            body = resp.data.decode("utf-8", errors="replace")
            tb = ""
            try:
                j = _json.loads(body)
                tb = ((j.get("error") or {}).get("details") or {}).get("traceback", "")
            except Exception: pass
            if not tb: tb = next((l.strip() for l in body.splitlines() if l.strip()), "(empty)")
            return (src, url, resp.status_code, tb)

        skip_prefixes = ("/static/", "/_debug_toolbar/")
        rules = [r for r in _app.url_map.iter_rules() if "GET" in r.methods and "<" not in r.rule and not any(r.rule.startswith(p) for p in skip_prefixes)]
        raw = []
        for rule in sorted(rules, key=lambda r: r.rule):
            r = _capture("url", rule.rule, (200, 302, 403, 404, 405))
            if r: raw.append(r)
        for key in sorted(_api_registry.keys()):
            r = _capture("api", f"/api/{key}/", (200, 403))
            if r: raw.append(r)

        if not raw:
            click.echo("[test errors] all clear")
            return

        groups = {}
        for src, url, status, tb in raw:
            exc, loc = _parse_tb(tb)
            key = re.sub(r'line \d+', 'line N', exc); key = re.sub(r':\d+', ':N', key); key = key[:120]
            groups.setdefault(key, []).append((f"[{src}] {url}", loc))

        click.echo(f"\n[test errors] {len(raw)} failures, {len(groups)} causes\n")
        for exc_key, entries in groups.items():
            click.echo(f"ERROR  {exc_key}")
            for url_str, _ in entries: click.echo(f"       {url_str}")
            click.echo()
