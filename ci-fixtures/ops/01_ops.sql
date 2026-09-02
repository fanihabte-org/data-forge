create schema ops;

create table ops.carriers
(
    carrier_code       varchar(15)   not null,
    carrier_name       varchar(120)  not null,
    mode               varchar(10)   not null,
    cost_index         numeric(6, 3) not null,
    published_otd_rate numeric(5, 3) not null,
    created_at         timestamp     not null,
    updated_at         timestamp     not null,
    dw_run_timestamp   timestamp     not null,
    constraint cpk_carriers
        primary key (carrier_code, updated_at)
);

create table ops.customers
(
    customer_id        integer        not null,
    account_number     varchar(20)    not null,
    customer_name      varchar(200)   not null,
    segment            varchar(40)    not null,
    industry           varchar(60)    not null,
    region             varchar(20)    not null,
    company_code       varchar(10)    not null,
    country            varchar(60)    not null,
    employee_count     integer        not null,
    credit_limit_usd   numeric(14, 2) not null,
    payment_terms_days smallint       not null,
    is_active          boolean        not null,
    created_at         timestamp      not null,
    updated_at         timestamp      not null,
    dw_run_timestamp   timestamp      not null,
    constraint pk_customers
        primary key (customer_id, updated_at)
);

create table ops.invoices
(
    invoice_id       bigint         not null,
    invoice_number   varchar(24)    not null,
    order_id         bigint         not null,
    currency_code    char(3)        not null,
    amount           numeric(18, 2) not null,
    status           varchar(20)    not null,
    invoice_date     date           not null,
    created_at       timestamp      not null,
    updated_at       timestamp      not null,
    dw_run_timestamp timestamp      not null,
    constraint pk_invoices
        primary key (invoice_id, updated_at)
);

create table ops.order_lines
(
    order_line_id    bigint         not null,
    order_id         bigint         not null,
    product_id       integer        not null,
    quantity         integer        not null,
    unit_price       numeric(16, 2) not null,
    discount_pct     numeric(5, 2)  not null,
    line_amount      numeric(18, 2) not null,
    unit_cost_usd    numeric(12, 2) not null,
    created_at       timestamp      not null,
    updated_at       timestamp      not null,
    dw_run_timestamp timestamp      not null,
    constraint pk_order_lines
        primary key (order_line_id, updated_at)
);

create table ops.orders
(
    order_id                bigint        not null,
    customer_id             integer       not null,
    opportunity_ref         varchar(18),
    rep_id                  varchar(12),
    order_date              date          not null,
    requested_delivery_date date          not null,
    currency_code           char(3)       not null,
    status                  varchar(20)   not null,
    sales_channel           varchar(20)   not null,
    order_discount_pct      numeric(5, 2) not null,
    po_number               varchar(20),
    created_at              timestamp     not null,
    updated_at              timestamp     not null,
    dw_run_timestamp        timestamp     not null,
    constraint pk_orders
        primary key (order_id, updated_at)
);

create table ops.products
(
    product_id        integer        not null,
    sku               varchar(40)    not null,
    product_name      varchar(200)   not null,
    category          varchar(60)    not null,
    product_family    varchar(40)    not null,
    list_price_usd    numeric(12, 2) not null,
    standard_cost_usd numeric(12, 2) not null,
    is_discontinued   boolean        not null,
    discontinued_on   date,
    launch_date       date           not null,
    created_at        timestamp      not null,
    updated_at        timestamp      not null,
    dw_run_timestamp  timestamp      not null,
    constraint pk_products
        primary key (product_id, updated_at)
);

create table ops.shipments
(
    shipment_id            bigint         not null,
    order_id               bigint         not null,
    warehouse_code         varchar(10)    not null,
    carrier_code           varchar(15)    not null,
    service_level          varchar(15)    not null,
    package_count          smallint       not null,
    gross_weight_kg        numeric(12, 2) not null,
    distance_km            numeric(12, 2) not null,
    freight_cost_usd       numeric(12, 2) not null,
    tracking_number        varchar(30)    not null,
    promised_delivery_date date           not null,
    ship_date              date           not null,
    delivered_date         date,
    created_at             timestamp      not null,
    updated_at             timestamp      not null,
    dw_run_timestamp       timestamp      not null,
    constraint pk_shipments
        primary key (shipment_id, updated_at)
);

create table ops.support_cases
(
    case_id          bigint      not null,
    customer_id      integer     not null,
    case_type        varchar(40) not null,
    priority         char(2)     not null,
    channel          varchar(20) not null,
    resolution_hours numeric(10, 2),
    status           varchar(20) not null,
    csat_score       smallint,
    assigned_region  varchar(20) not null,
    opened_at        timestamp   not null,
    created_at       timestamp   not null,
    updated_at       timestamp   not null,
    dw_run_timestamp timestamp   not null,
    constraint pk_cases
        primary key (case_id, updated_at)
);

create table ops.warehouses
(
    warehouse_code   varchar(10)   not null,
    warehouse_name   varchar(120)  not null,
    region           varchar(20)   not null,
    latitude         numeric(9, 5) not null,
    longitude        numeric(9, 5) not null,
    created_at       timestamp     not null,
    updated_at       timestamp     not null,
    dw_run_timestamp timestamp     not null,
    constraint pk_warehouses
        primary key (warehouse_code, updated_at)
);

create table ops.invoice_status_history
(
    invoice_status_event_id bigint      not null primary key,
    invoice_id              bigint      not null,
    previous_status         varchar(20),
    new_status              varchar(20) not null,
    occurred_at             timestamp   not null,
    recorded_at             timestamp   not null,
    source_event_id         varchar(64) not null,
    sla_due_at              timestamp,
    sla_status              varchar(10) not null,
    anomaly_type            varchar(80),
    dw_run_timestamp        timestamp   not null
);

create table ops.order_status_history
(
    order_status_event_id bigint      not null primary key,
    order_id              bigint      not null,
    previous_status       varchar(20),
    new_status            varchar(20) not null,
    occurred_at           timestamp   not null,
    recorded_at           timestamp   not null,
    source_event_id       varchar(64) not null,
    sla_due_at            timestamp,
    sla_status            varchar(10) not null,
    anomaly_type          varchar(80),
    dw_run_timestamp      timestamp   not null
);

create table ops.shipment_status_history
(
    shipment_status_event_id bigint      not null primary key,
    shipment_id              bigint      not null,
    previous_status          varchar(20),
    new_status               varchar(20) not null,
    occurred_at              timestamp   not null,
    recorded_at              timestamp   not null,
    source_event_id          varchar(64) not null,
    sla_due_at               timestamp,
    sla_status               varchar(10) not null,
    anomaly_type             varchar(80),
    dw_run_timestamp         timestamp   not null
);

create table ops.support_case_status_history
(
    support_case_status_event_id bigint      not null primary key,
    case_id                      bigint      not null,
    previous_status              varchar(20),
    new_status                   varchar(20) not null,
    occurred_at                  timestamp   not null,
    recorded_at                  timestamp   not null,
    source_event_id              varchar(64) not null,
    sla_due_at                   timestamp,
    sla_status                   varchar(10) not null,
    anomaly_type                 varchar(80),
    dw_run_timestamp             timestamp   not null
);


