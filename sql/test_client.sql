
CREATE TABLE IF NOT EXISTS invoice(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number varchar(255),
    invoice_date varchar(255),
    vendor_name varchar(255),
    vendor_number varchar(20),
    address varchar(255),
    city varchar(100),
    state varchar(100),
    country varchar(255),
    zip_code varchar(10),
    tax_percent varchar(10),
    tax_amount varchar(255),
    discount_percent varchar(10),
    discount_amount varchar(255),
    vat_percent varchar(10),
    vat_amount varchar(255),
    bank_name varchar(255),
    bank_account_number varchar(255),
    gross_amount varchar(255),
    net_amount varchar(255)
);

CREATE TABLE IF NOT EXISTS invoice_line_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number varchar(255),
    item_name varchar(255),
    item_quantity varchar(255),
    unit_price varchar(255),
    total_price varchar(255)
);

