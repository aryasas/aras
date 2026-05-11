import os
from flask import Flask
from arasCore import create_app
from arasCore.lib.services.openapi import generate_openapi_spec
import json

app = create_app()

with app.app_context():
    spec = generate_openapi_spec()
    print(json.dumps(spec, indent=2))
