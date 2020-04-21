--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.17
-- Dumped by pg_dump version 9.6.17

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

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: applications; Type: TABLE; Schema: public; Owner: pi
--

CREATE TABLE public.applications (
    name character varying(30) NOT NULL,
    app_key character varying(30) NOT NULL,
    username character varying(30),
    description character varying(200)
);


-- ALTER TABLE public.applications OWNER TO pi;

--
-- Name: pend_msgs; Type: TABLE; Schema: public; Owner: pi
--

CREATE TABLE public.pend_msgs (
    app_key character varying(30) NOT NULL,
    dev_id numeric(3,0) NOT NULL,
    msg character varying(150) NOT NULL,
    ack boolean DEFAULT false NOT NULL
);


-- ALTER TABLE public.pend_msgs OWNER TO pi;

--
-- Name: users; Type: TABLE; Schema: public; Owner: pi
--

CREATE TABLE public.users (
    name character varying(30) NOT NULL,
    password character varying(100) NOT NULL
);


-- ALTER TABLE public.users OWNER TO pi;

--
-- Name: applications applications_app_key_key; Type: CONSTRAINT; Schema: public; Owner: pi
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_app_key_key UNIQUE (app_key);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: pi
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (name, app_key);

--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: pi
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (name);


--
-- Name: applications applications_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pi
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_username_fkey FOREIGN KEY (username) REFERENCES public.users(name);


--
-- PostgreSQL database dump complete
--

