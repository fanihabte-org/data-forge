create schema crm;

create table crm.account
(
    id                varchar(18)  not null,
    name              varchar(200) not null,
    accountnumber     varchar(20)  not null,
    industry          varchar(60),
    type              varchar(40),
    billingcountry    varchar(60),
    annualrevenue     numeric(18, 2),
    numberofemployees integer,
    ownerid           varchar(12),
    isdeleted         boolean      not null,
    createddate       varchar(30)  not null,
    lastmodifieddate  varchar(30)  not null,
    dw_run_timestamp  timestamp    not null,
    constraint pk_account
        primary key (id, lastmodifieddate)
);

create table crm.opportunity
(
    id               varchar(18)  not null,
    accountid        varchar(18)  not null,
    name             varchar(260) not null,
    stagename        varchar(40)  not null,
    amount           numeric(18, 2),
    currencyisocode  char(3)      not null,
    probability      smallint     not null,
    leadsource       varchar(40),
    campaignid       varchar(12),
    discountpercent  numeric(5, 2),
    lossreason       varchar(40),
    salescycledays   integer,
    ownerid          varchar(12),
    closedate        date         not null,
    createddate      varchar(30)  not null,
    lastmodifieddate varchar(30)  not null,
    isdeleted        boolean      not null,
    dw_run_timestamp timestamp    not null,
    constraint pk_opportunity
        primary key (id, lastmodifieddate)
);
