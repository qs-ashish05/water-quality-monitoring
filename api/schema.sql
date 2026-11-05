CREATE TABLE water_quality (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    generated_at        TIMESTAMPTZ NOT NULL UNIQUE,

    temperature         NUMERIC(6,2),
    temperature_tag     VARCHAR(100),
    temperature_safe    BOOLEAN,

    conductivity        NUMERIC(10,2),
    conductivity_tag    VARCHAR(100),
    conductivity_safe   BOOLEAN,

    ph                  NUMERIC(4,2),
    ph_tag              VARCHAR(100),
    ph_safe             BOOLEAN,

    colour              NUMERIC(6,2),
    colour_tag          VARCHAR(100),
    colour_safe         BOOLEAN,

    dissolved_oxygen    NUMERIC(6,2),
    do_tag              VARCHAR(100),
    do_safe             BOOLEAN,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);