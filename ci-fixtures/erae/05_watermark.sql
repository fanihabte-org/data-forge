create table pipeline_run.watermark_logs_archive
(
    source_system     varchar(50),
    table_name        varchar(50),
    schema_name       varchar(50),
    marking_column    varchar(50),
    highest_watermark timestamp,
    dw_run_timestamp  timestamp
);

create table pipeline_run.watermark_logs
(
    source_system     varchar(50),
    table_name        varchar(50) not null
        primary key,
    schema_name       varchar(50),
    marking_column    varchar(50),
    highest_watermark timestamp,
    dw_run_timestamp  timestamp
);
