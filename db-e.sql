CREATE TABLE public.notifications (
	id VARCHAR(10) UNIQUE NOT NULL,
	app_key VARCHAR(30) UNIQUE NOT NULL,
	dev_id NUMERIC(3) NOT NULL,
	name VARCHAR(50) NOT NULL,
	description VARCHAR(300),
	action_type VARCHAR(20) NOT NULL,
	action VARCHAR (200) NOT NULL
);

CREATE TABLE public.notifications_queue (
	nf_id VARCHAR(10) NOT NULL,
	app_key VARCHAR(30) NOT NULL,
	dev_id NUMERIC(3) NOT NULL
);

ALTER TABLE ONLY public.notifications
	ADD CONSTRAINT notifications_pkey PRIMARY KEY (id, app_key, dev_id);

ALTER TABLE ONLY public.notifications_queue
	ADD CONSTRAINT notifications_queue_pkey PRIMARY KEY (nf_id, app_key, dev_id);

ALTER TABLE ONLY public.notifications
	ADD CONSTRAINT notifications_app_key_fkey FOREIGN KEY (app_key) REFERENCES public.applications(app_key);

ALTER TABLE ONLY public.notifications_queue
	ADD CONSTRAINT notifications_queue_app_key_fkey FOREIGN KEY (app_key) REFERENCES public.notifications(app_key);

ALTER TABLE ONLY public.notifications_queue
	ADD CONSTRAINT notifications_queue_nf_id_fkey FOREIGN KEY (nf_id) REFERENCES public.notifications(id);

