create schema erp;

create table erp.companies
(
    company_code        varchar(10)  not null,
    company_name        varchar(120) not null,
    functional_currency char(3)      not null,
    country             varchar(60)  not null,
    created_at          timestamp    not null,
    updated_at          timestamp    not null,
    dw_run_timestamp    timestamp    not null,
    constraint pk_companies
        primary key (company_code, updated_at)
);

create table erp.cost_centers
(
    cost_center_code varchar(20)  not null,
    cost_center_name varchar(120) not null,
    company_code     varchar(10)  not null,
    region           varchar(20)  not null,
    function         varchar(40)  not null,
    owner_email      varchar(160) not null,
    is_active        boolean      not null,
    valid_from       date         not null,
    valid_to         date,
    created_at       timestamp    not null,
    updated_at       timestamp    not null,
    dw_run_timestamp timestamp    not null,
    constraint pk_cost_centers
        primary key (cost_center_code, updated_at)
);

create table erp.fx_rates
(
    from_currency    char(3)        not null,
    to_currency      char(3)        not null,
    rate_type        varchar(10)    not null,
    rate             numeric(18, 8) not null,
    source_system    varchar(30)    not null,
    rate_date        date           not null,
    loaded_at        timestamp      not null,
    created_at       timestamp      not null,
    updated_at       timestamp      not null,
    dw_run_timestamp timestamp      not null,
    constraint pk_fx_rates
        primary key (from_currency, to_currency, rate_type, rate_date, updated_at)
);

create table erp.gl_accounts
(
    gl_account       varchar(10)  not null,
    gl_name          varchar(120) not null,
    account_type     varchar(20)  not null,
    is_postable      boolean      not null,
    created_at       timestamp    not null,
    updated_at       timestamp    not null,
    dw_run_timestamp timestamp    not null,
    constraint pk_gl_accounts
        primary key (gl_account, updated_at)
);

create table erp.revenue_postings
(
    posting_id          bigint         not null,
    document_number     varchar(24)    not null,
    document_type       varchar(10)    not null,
    company_code        varchar(10)    not null,
    order_ref           bigint,
    reverses_posting_id bigint,
    gl_account          varchar(10)    not null,
    cost_center_code    varchar(20),
    document_currency   char(3)        not null,
    company_currency    char(3)        not null,
    amount_doc          numeric(18, 2) not null,
    amount_company      numeric(18, 2) not null,
    fiscal_period       varchar(7)     not null,
    posting_date        date           not null,
    posted_at           timestamp      not null,
    created_at          timestamp      not null,
    dw_run_timestamp    timestamp      not null,
    constraint pk_postings
        primary key (posting_id, posted_at)
);
