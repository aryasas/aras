
from run import app
with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'dev' in rule.endpoint:
            print(f"{rule.endpoint} -> {rule.rule}")
