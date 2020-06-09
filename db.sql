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
    username character varying(30) NOT NULL,
    description character varying(200),
    secure boolean DEFAULT false NOT NULL,
    secure_key character varying(100) NOT NULL
);


-- ALTER TABLE public.applications OWNER TO pi;

--
-- Name: pend_msgs; Type: TABLE; Schema: public; Owner: pi
--

CREATE TABLE public.pend_msgs (
    app_key character varying(30) NOT NULL,
    dev_id numeric(3,0) NOT NULL,
    msg character varying(150) NOT NULL,
    ack boolean DEFAULT false NOT NULL,
    sent_at timestamp(6) DEFAULT now(),
    confirmed_at timestamp(6)
);


-- ALTER TABLE public.pend_msgs OWNER TO pi;

--
-- Name: users; Type: TABLE; Schema: public; Owner: pi
--

CREATE TABLE public.users (
--    first_name character varying(50),
--    last_name character varying(50),
    name character varying(30) NOT NULL,
    password character varying(100) NOT NULL,
    role character varying(10) NOT NULL
);


-- ALTER TABLE public.notifications OWNER TO pi;

--
-- Name: users; Type: TABLE; Schema: public; Owner: pi
--
CREATE TABLE public.notifications (
	id character varying(10) NOT NULL,
	app_key character varying(30) NOT NULL,
	dev_id numeric(3) NOT NULL,
	name character varying(50) NOT NULL,
	description character varying(300),
	action_type character varying(20) NOT NULL,
	action character varying (200) NOT NULL
);

-- ALTER TABLE public.notifications_queue OWNER TO pi;

--
-- Name: users; Type: TABLE; Schema: public; Owner: pi
--
CREATE TABLE public.notifications_queue (
	nf_id character varying(10) NOT NULL,
	app_key character varying(30) NOT NULL,
	dev_id numeric(3) NOT NULL,
	fired_on timestamp(6) NOT NULL DEFAULT now()
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
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: pi
--
ALTER TABLE ONLY public.notifications
	ADD CONSTRAINT notifications_pkey PRIMARY KEY (id, app_key, dev_id);

--
-- Name: notifications notifications_app_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pi
--
ALTER TABLE ONLY public.notifications
	ADD CONSTRAINT notifications_app_key_fkey FOREIGN KEY (app_key) REFERENCES public.applications(app_key);

--
-- Name: notifications notifications_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: pi
--
ALTER TABLE ONLY public.notifications_queue
	ADD CONSTRAINT notifications_queue_pkey PRIMARY KEY (nf_id, app_key, dev_id);

--
-- Name: notifications_queue notifications_queue_app_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pi
--
ALTER TABLE ONLY public.notifications_queue
	ADD CONSTRAINT notifications_queue_app_key_fkey FOREIGN KEY (app_key, nf_id, dev_id) REFERENCES public.notifications(app_key, id, dev_id);


INSERT INTO public.users VALUES('admin', '$2b$12$chdF4ji1maIRLd4ms4s4yugFv.2BTvOAwiaWi6iRlTJzlGKjpTcA.', 'superuser')

