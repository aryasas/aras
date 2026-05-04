import logging

# Simulate incoming request data similar to the error logs
form_data = {
    "barcode": ["Kopi Bean", "Kopi Bean"],
    "uom_id": ["6", "5", "5", "", "", "", ""],
    "is_active": ["on", "on"],
    "factor": ["1", "1"],
    "created_by_id": 1,
    "product_id": 11,
    "updated_by_id": 1
}

def sanitize(raw_data):
    data = {}
    for key, val in raw_data.items():
        # Simulate form.getlist behavior
        if isinstance(val, list):
            data[key] = val[-1] if val else None
        else:
            data[key] = val
    return data

sanitized = sanitize(form_data)
print(f"Sanitized: {sanitized}")
