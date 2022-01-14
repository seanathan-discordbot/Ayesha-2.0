--
-- PostgreSQL database dump
--

-- Dumped from database version 13.5
-- Dumped by pg_dump version 13.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: acolytes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.acolytes (
    acolyte_id bigint NOT NULL,
    user_id bigint NOT NULL,
    acolyte_name character varying(20) NOT NULL,
    xp integer DEFAULT 0 NOT NULL,
    duplicate smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.acolytes OWNER TO postgres;

--
-- Name: Acolytes_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Acolytes_instance_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Acolytes_instance_id_seq" OWNER TO postgres;

--
-- Name: Acolytes_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Acolytes_instance_id_seq" OWNED BY public.acolytes.acolyte_id;


--
-- Name: associations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.associations (
    assc_id bigint NOT NULL,
    assc_name character varying(32) NOT NULL,
    assc_type character varying(15) NOT NULL,
    assc_xp integer DEFAULT 0 NOT NULL,
    leader_id bigint NOT NULL,
    assc_desc character varying(256),
    assc_icon text NOT NULL,
    join_status character varying(8) DEFAULT 'open'::character varying NOT NULL,
    base character varying(15),
    base_set boolean DEFAULT false,
    min_level smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.associations OWNER TO postgres;

--
-- Name: Guilds_guild_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Guilds_guild_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Guilds_guild_id_seq" OWNER TO postgres;

--
-- Name: Guilds_guild_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Guilds_guild_id_seq" OWNED BY public.associations.assc_id;


--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    item_id bigint NOT NULL,
    weapontype character varying(15) NOT NULL,
    user_id bigint NOT NULL,
    attack smallint NOT NULL,
    crit smallint NOT NULL,
    weapon_name character varying(20) NOT NULL,
    rarity character varying(10) NOT NULL
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: Items_item_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Items_item_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Items_item_id_seq" OWNER TO postgres;

--
-- Name: Items_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Items_item_id_seq" OWNED BY public.items.item_id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.players (
    num bigint NOT NULL,
    user_id bigint NOT NULL,
    user_name character varying(32) NOT NULL,
    xp integer DEFAULT 0 NOT NULL,
    equipped_item integer,
    acolyte1 integer,
    acolyte2 integer,
    assc integer,
    guild_rank character varying(8),
    gold integer DEFAULT 500 NOT NULL,
    occupation character varying(20),
    origin character varying(20),
    loc character varying(20) DEFAULT 'Aramithea'::character varying NOT NULL,
    pvpwins integer DEFAULT 0 NOT NULL,
    pvpfights integer DEFAULT 0 NOT NULL,
    bosswins integer DEFAULT 0 NOT NULL,
    bossfights integer DEFAULT 0 NOT NULL,
    rubidics integer DEFAULT 10 NOT NULL,
    pitycounter smallint DEFAULT 0 NOT NULL,
    adventure bigint,
    destination character varying(20),
    gravitas integer DEFAULT 0 NOT NULL,
    pve_limit smallint DEFAULT 25 NOT NULL,
    CONSTRAINT check_positive CHECK ((gravitas >= 0))
);


ALTER TABLE public.players OWNER TO postgres;

--
-- Name: Players_num_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Players_num_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Players_num_seq" OWNER TO postgres;

--
-- Name: Players_num_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Players_num_seq" OWNED BY public.players.num;


--
-- Name: accessories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accessories (
    accessory_id bigint NOT NULL,
    accessory_type character varying(16) NOT NULL,
    accessory_name character varying(16) NOT NULL,
    user_id bigint NOT NULL,
    prefix character varying(16) NOT NULL
);


ALTER TABLE public.accessories OWNER TO postgres;

--
-- Name: accessories_accessory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.accessories_accessory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accessories_accessory_id_seq OWNER TO postgres;

--
-- Name: accessories_accessory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.accessories_accessory_id_seq OWNED BY public.accessories.accessory_id;


--
-- Name: area_attacks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.area_attacks (
    id bigint NOT NULL,
    area character varying(15) NOT NULL,
    attacker bigint,
    defender bigint,
    winner bigint,
    battle_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.area_attacks OWNER TO postgres;

--
-- Name: area_attacks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.area_attacks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.area_attacks_id_seq OWNER TO postgres;

--
-- Name: area_attacks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.area_attacks_id_seq OWNED BY public.area_attacks.id;


--
-- Name: area_control; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.area_control (
    id bigint NOT NULL,
    area character varying(15) NOT NULL,
    owner bigint,
    reign_begin timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.area_control OWNER TO postgres;

--
-- Name: area_control_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.area_control_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.area_control_id_seq OWNER TO postgres;

--
-- Name: area_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.area_control_id_seq OWNED BY public.area_control.id;


--
-- Name: armor; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.armor (
    armor_id bigint NOT NULL,
    armor_type character varying(16) NOT NULL,
    armor_slot character varying(10) NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.armor OWNER TO postgres;

--
-- Name: armor_armor_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.armor_armor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.armor_armor_id_seq OWNER TO postgres;

--
-- Name: armor_armor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.armor_armor_id_seq OWNED BY public.armor.armor_id;


--
-- Name: brotherhood_champions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brotherhood_champions (
    id bigint NOT NULL,
    assc_id bigint NOT NULL,
    champ1 bigint,
    champ2 bigint,
    champ3 bigint
);


ALTER TABLE public.brotherhood_champions OWNER TO postgres;

--
-- Name: brotherhood_champions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.brotherhood_champions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.brotherhood_champions_id_seq OWNER TO postgres;

--
-- Name: brotherhood_champions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.brotherhood_champions_id_seq OWNED BY public.brotherhood_champions.id;


--
-- Name: class_estate; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.class_estate (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    name character varying(32) DEFAULT 'My Practice'::character varying,
    type character varying(15),
    adventure bigint,
    image text
);


ALTER TABLE public.class_estate OWNER TO postgres;

--
-- Name: class_estate_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.class_estate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.class_estate_id_seq OWNER TO postgres;

--
-- Name: class_estate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.class_estate_id_seq OWNED BY public.class_estate.id;


--
-- Name: comptroller_bonuses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.comptroller_bonuses (
    id bigint NOT NULL,
    comptroller_id bigint NOT NULL,
    bonus smallint,
    bonus_xp integer DEFAULT 0 NOT NULL,
    is_set boolean DEFAULT false,
    assc_id bigint
);


ALTER TABLE public.comptroller_bonuses OWNER TO postgres;

--
-- Name: comptroller_bonuses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.comptroller_bonuses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.comptroller_bonuses_id_seq OWNER TO postgres;

--
-- Name: comptroller_bonuses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.comptroller_bonuses_id_seq OWNED BY public.comptroller_bonuses.id;


--
-- Name: equips; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equips (
    user_id bigint NOT NULL,
    helmet integer,
    bodypiece integer,
    boots integer,
    accessory integer
);


ALTER TABLE public.equips OWNER TO postgres;

--
-- Name: guild_bank_account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.guild_bank_account (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    account_funds bigint DEFAULT 0 NOT NULL
);


ALTER TABLE public.guild_bank_account OWNER TO postgres;

--
-- Name: guild_bank_account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.guild_bank_account_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.guild_bank_account_id_seq OWNER TO postgres;

--
-- Name: guild_bank_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.guild_bank_account_id_seq OWNED BY public.guild_bank_account.id;


--
-- Name: guild_membercount; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.guild_membercount AS
 SELECT players.assc AS guild_id,
    count(*) AS member_count
   FROM public.players
  GROUP BY players.assc;


ALTER TABLE public.guild_membercount OWNER TO postgres;

--
-- Name: officeholders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.officeholders (
    id bigint NOT NULL,
    officeholder bigint NOT NULL,
    office character varying(12) NOT NULL,
    setdate date DEFAULT CURRENT_DATE
);


ALTER TABLE public.officeholders OWNER TO postgres;

--
-- Name: officeholders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.officeholders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.officeholders_id_seq OWNER TO postgres;

--
-- Name: officeholders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.officeholders_id_seq OWNED BY public.officeholders.id;


--
-- Name: prefixes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prefixes (
    server bigint,
    prefix character varying(10) DEFAULT '%'::character varying NOT NULL
);


ALTER TABLE public.prefixes OWNER TO postgres;

--
-- Name: reminders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reminders (
    id bigint NOT NULL,
    starttime bigint NOT NULL,
    endtime bigint NOT NULL,
    user_id bigint NOT NULL,
    content character varying(255)
);


ALTER TABLE public.reminders OWNER TO postgres;

--
-- Name: reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reminders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reminders_id_seq OWNER TO postgres;

--
-- Name: reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reminders_id_seq OWNED BY public.reminders.id;


--
-- Name: resources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resources (
    user_id bigint NOT NULL,
    fur integer DEFAULT 0 NOT NULL,
    bone integer DEFAULT 0 NOT NULL,
    iron integer DEFAULT 0 NOT NULL,
    silver integer DEFAULT 0 NOT NULL,
    wood integer DEFAULT 0 NOT NULL,
    wheat integer DEFAULT 0 NOT NULL,
    oat integer DEFAULT 0 NOT NULL,
    reeds integer DEFAULT 0 NOT NULL,
    pine integer DEFAULT 0 NOT NULL,
    moss integer DEFAULT 0 NOT NULL,
    cacao integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.resources OWNER TO postgres;

--
-- Name: strategy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.strategy (
    user_id bigint NOT NULL,
    attack smallint DEFAULT 60 NOT NULL,
    block smallint DEFAULT 15 NOT NULL,
    parry smallint DEFAULT 15 NOT NULL,
    heal smallint DEFAULT 5 NOT NULL,
    bide smallint DEFAULT 5 NOT NULL
);


ALTER TABLE public.strategy OWNER TO postgres;

--
-- Name: tax_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_rates (
    id bigint NOT NULL,
    tax_rate numeric(3,2) DEFAULT 5 NOT NULL,
    setby bigint,
    setdate timestamp without time zone DEFAULT now()
);


ALTER TABLE public.tax_rates OWNER TO postgres;

--
-- Name: tax_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tax_rates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tax_rates_id_seq OWNER TO postgres;

--
-- Name: tax_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tax_rates_id_seq OWNED BY public.tax_rates.id;


--
-- Name: tax_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_transactions (
    id bigint NOT NULL,
    "time" timestamp without time zone DEFAULT now(),
    user_id bigint NOT NULL,
    before_tax integer NOT NULL,
    tax_amount integer NOT NULL,
    tax_rate numeric(3,2)
);


ALTER TABLE public.tax_transactions OWNER TO postgres;

--
-- Name: tax_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tax_transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tax_transactions_id_seq OWNER TO postgres;

--
-- Name: tax_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tax_transactions_id_seq OWNED BY public.tax_transactions.id;


--
-- Name: accessories accessory_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accessories ALTER COLUMN accessory_id SET DEFAULT nextval('public.accessories_accessory_id_seq'::regclass);


--
-- Name: acolytes acolyte_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acolytes ALTER COLUMN acolyte_id SET DEFAULT nextval('public."Acolytes_instance_id_seq"'::regclass);


--
-- Name: area_attacks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_attacks ALTER COLUMN id SET DEFAULT nextval('public.area_attacks_id_seq'::regclass);


--
-- Name: area_control id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_control ALTER COLUMN id SET DEFAULT nextval('public.area_control_id_seq'::regclass);


--
-- Name: armor armor_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.armor ALTER COLUMN armor_id SET DEFAULT nextval('public.armor_armor_id_seq'::regclass);


--
-- Name: associations assc_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associations ALTER COLUMN assc_id SET DEFAULT nextval('public."Guilds_guild_id_seq"'::regclass);


--
-- Name: brotherhood_champions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions ALTER COLUMN id SET DEFAULT nextval('public.brotherhood_champions_id_seq'::regclass);


--
-- Name: class_estate id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate ALTER COLUMN id SET DEFAULT nextval('public.class_estate_id_seq'::regclass);


--
-- Name: comptroller_bonuses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comptroller_bonuses ALTER COLUMN id SET DEFAULT nextval('public.comptroller_bonuses_id_seq'::regclass);


--
-- Name: guild_bank_account id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account ALTER COLUMN id SET DEFAULT nextval('public.guild_bank_account_id_seq'::regclass);


--
-- Name: items item_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN item_id SET DEFAULT nextval('public."Items_item_id_seq"'::regclass);


--
-- Name: officeholders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officeholders ALTER COLUMN id SET DEFAULT nextval('public.officeholders_id_seq'::regclass);


--
-- Name: players num; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players ALTER COLUMN num SET DEFAULT nextval('public."Players_num_seq"'::regclass);


--
-- Name: reminders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reminders ALTER COLUMN id SET DEFAULT nextval('public.reminders_id_seq'::regclass);


--
-- Name: tax_rates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates ALTER COLUMN id SET DEFAULT nextval('public.tax_rates_id_seq'::regclass);


--
-- Name: tax_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_transactions ALTER COLUMN id SET DEFAULT nextval('public.tax_transactions_id_seq'::regclass);


--
-- Name: acolytes Acolytes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acolytes
    ADD CONSTRAINT "Acolytes_pkey" PRIMARY KEY (acolyte_id);


--
-- Name: associations Guilds_guild_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT "Guilds_guild_name_key" UNIQUE (assc_name);


--
-- Name: associations Guilds_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associations
    ADD CONSTRAINT "Guilds_pkey" PRIMARY KEY (assc_id);


--
-- Name: items Items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT "Items_pkey" PRIMARY KEY (item_id);


--
-- Name: players Players_acolyte1_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_acolyte1_key" UNIQUE (acolyte1);


--
-- Name: players Players_acolyte2_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_acolyte2_key" UNIQUE (acolyte2);


--
-- Name: players Players_equipped_item_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_equipped_item_key" UNIQUE (equipped_item);


--
-- Name: players Players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_pkey" PRIMARY KEY (num);


--
-- Name: players Players_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_user_id_key" UNIQUE (user_id);


--
-- Name: resources Resources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT "Resources_pkey" PRIMARY KEY (user_id);


--
-- Name: accessories accessories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accessories
    ADD CONSTRAINT accessories_pkey PRIMARY KEY (accessory_id);


--
-- Name: area_attacks area_attacks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_attacks
    ADD CONSTRAINT area_attacks_pkey PRIMARY KEY (id);


--
-- Name: area_control area_control_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_control
    ADD CONSTRAINT area_control_pkey PRIMARY KEY (id);


--
-- Name: armor armor_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.armor
    ADD CONSTRAINT armor_pkey PRIMARY KEY (armor_id);


--
-- Name: brotherhood_champions brotherhood_champions_guild_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions
    ADD CONSTRAINT brotherhood_champions_guild_id_key UNIQUE (assc_id);


--
-- Name: brotherhood_champions brotherhood_champions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions
    ADD CONSTRAINT brotherhood_champions_pkey PRIMARY KEY (id);


--
-- Name: class_estate class_estate_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate
    ADD CONSTRAINT class_estate_pkey PRIMARY KEY (id);


--
-- Name: class_estate class_estate_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate
    ADD CONSTRAINT class_estate_user_id_key UNIQUE (user_id);


--
-- Name: comptroller_bonuses comptroller_bonuses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comptroller_bonuses
    ADD CONSTRAINT comptroller_bonuses_pkey PRIMARY KEY (id);


--
-- Name: equips equips_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equips
    ADD CONSTRAINT equips_pkey PRIMARY KEY (user_id);


--
-- Name: guild_bank_account guild_bank_account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account
    ADD CONSTRAINT guild_bank_account_pkey PRIMARY KEY (id);


--
-- Name: guild_bank_account guild_bank_account_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account
    ADD CONSTRAINT guild_bank_account_user_id_key UNIQUE (user_id);


--
-- Name: officeholders officeholders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officeholders
    ADD CONSTRAINT officeholders_pkey PRIMARY KEY (id);


--
-- Name: reminders reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reminders
    ADD CONSTRAINT reminders_pkey PRIMARY KEY (id);


--
-- Name: strategy strategy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.strategy
    ADD CONSTRAINT strategy_pkey PRIMARY KEY (user_id);


--
-- Name: tax_rates tax_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT tax_rates_pkey PRIMARY KEY (id);


--
-- Name: tax_transactions tax_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_transactions
    ADD CONSTRAINT tax_transactions_pkey PRIMARY KEY (id);


--
-- Name: prefixes uniqueserver; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prefixes
    ADD CONSTRAINT uniqueserver UNIQUE (server);


--
-- Name: strategy strategy_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.strategy
    ADD CONSTRAINT strategy_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.players(user_id);


--
-- PostgreSQL database dump complete
--

