# split_sql.py
import re

DOMAIN_TABLES = {
    "healthcare": {"raw_patients", "staging_patients", "mart_billing", "mart_demographics"},
    "fiction-retail": {"customers", "inventory", "order_items", "orders", "products",
                        "promotions", "returns", "shipments", "suppliers", "warehouses"},
    "nyc-taxi": {"raw_trips", "staging_trips", "mart_daily_summary"},
}

with open("full_remediation.sql", "r") as f:
    content = f.read()

# Разбиваем по блокам, каждый начинается с "-- ====...=" перед "-- Target Table:"
blocks = re.split(r"(?=-- =+\n-- Albugent)", content)

domain_output = {domain: [] for domain in DOMAIN_TABLES}

for block in blocks:
    match = re.search(r"-- Target Table: (\w+)", block)
    if not match:
        continue
    table_name = match.group(1)
    for domain, tables in DOMAIN_TABLES.items():
        if table_name in tables:
            domain_output[domain].append(block.strip())
            break

for domain, blocks_list in domain_output.items():
    filename = f"test_run/{domain.replace('-', '_')}.sql"
    with open(filename, "w") as f:
        f.write("\n\n".join(blocks_list))
    print(f"Written {filename} with {len(blocks_list)} table blocks")