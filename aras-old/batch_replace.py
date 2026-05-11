import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if "db.Column" not in content:
        return False

    # Add Col and type imports if missing but db.Column is present
    if "from arasCore.lib.core import" not in content and "from arasCore.ArasGen import" not in content:
        if "from arasCore.lib.core.base_model import ArasModel" in content:
            content = content.replace("from arasCore.lib.core.base_model import ArasModel",
                                      "from arasCore.lib.core.base_model import ArasModel\nfrom arasCore.lib.core import Col, String, Text, Integer, Decimal, Float, Boolean, Date, DateTime, FK")
        elif "from .lib.core.base_model import ArasModel" in content:
            content = content.replace("from .lib.core.base_model import ArasModel",
                                      "from .lib.core.base_model import ArasModel\nfrom .lib.core import Col, String, Text, Integer, Decimal, Float, Boolean, Date, DateTime, FK")

    # Replacement patterns
    # db.Column(db.String(XX), ...) -> Col(String, ...)
    content = re.sub(r'db\.Column\(\s*db\.String(?:\(\d+\))?\s*,?', r'Col(String,', content)
    content = re.sub(r'db\.Column\(\s*db\.Text\s*,?', r'Col(Text,', content)
    content = re.sub(r'db\.Column\(\s*db\.Integer\s*,?', r'Col(Integer,', content)
    content = re.sub(r'db\.Column\(\s*db\.BigInteger\s*,?', r'Col(Integer,', content)
    content = re.sub(r'db\.Column\(\s*db\.Numeric(?:\([\d,\s]+\))?\s*,?', r'Col(Decimal,', content)
    content = re.sub(r'db\.Column\(\s*db\.Float\s*,?', r'Col(Float,', content)
    content = re.sub(r'db\.Column\(\s*db\.Boolean\s*,?', r'Col(Boolean,', content)
    content = re.sub(r'db\.Column\(\s*db\.Date\s*,?', r'Col(Date,', content)
    content = re.sub(r'db\.Column\(\s*db\.DateTime\s*,?', r'Col(DateTime,', content)

    # Fix nullable=False to null=False, nullable=True to null=True
    content = content.replace("nullable=False", "null=False")
    content = content.replace("nullable=True", "null=True")
    content = content.replace("primary_key=True", "primary=True")
    content = content.replace("autoincrement=True", "")

    # db.ForeignKey("...")
    content = re.sub(r'db\.ForeignKey\((["\'].*?["\'])\)', r'fk=\1', content)

    # db.func.now() -> should ideally be left alone or removed if we use _now or default
    # If it ends with `Col(Type, fk="..."),` we should fix it to Col(FK, fk="...")
    content = re.sub(r'Col\(\s*(?:String|Integer|BigInteger|DateTime|Date|Boolean|Decimal|Float|Text)\s*,\s*fk=(["\'].*?["\'])', r'Col(FK, fk=\1', content)

    # Clean up trailing commas in Col(...)
    content = re.sub(r'Col\(([^)]*?),\s*\)', r'Col(\1)', content)

    with open(filepath, 'w') as f:
        f.write(content)
    return True

target_dirs = ["arasCore", "aras"]
for d in target_dirs:
    for root, dirs, files in os.walk(d):
        for file in files:
            if file.endswith(".py"):
                process_file(os.path.join(root, file))

print("Batch replace completed.")
