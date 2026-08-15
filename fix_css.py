path = "frontend/css/dashboard.css"
with open(path, "r") as f:
    content = f.read()

old_block = """.barcode-row input {
    flex: 1 1 0;
    min-width: 0;
    width: auto;
    padding: 11px 12px;
    font-size: 15px;
    border: 1px solid #d8dde3;
    border-radius: 6px 0 0 6px;
    border-right: none;
}"""

new_block = """.barcode-row input {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    width: auto !important;
    padding: 11px 12px;
    font-size: 15px;
    border: 1px solid #d8dde3;
    border-radius: 6px 0 0 6px;
    border-right: none;
}"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, "w") as f:
        f.write(content)
    print("Replaced successfully.")
else:
    print("Old block not found — checking file manually needed.")
