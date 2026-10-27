CREATE SCHEMA IF NOT EXISTS ticket_notify;
CREATE TABLE IF NOT EXISTS ticket_notify.ticket_state (
 ticket_id bigint PRIMARY KEY, status_id bigint NOT NULL, status_name text NOT NULL,
 subject text NOT NULL, requester_email text, updated_on timestamptz NOT NULL,
 revision bigint NOT NULL DEFAULT 0, observed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ticket_notify.notifications (
 id bigserial PRIMARY KEY, ticket_id bigint NOT NULL, revision bigint NOT NULL,
 subject text NOT NULL, previous_status text NOT NULL, new_status text NOT NULL,
 recipient text, url text NOT NULL, state text NOT NULL CHECK(state IN ('pending','sending','sent','failed','suppressed')),
 reason text, created_at timestamptz NOT NULL DEFAULT now(), attempted_at timestamptz, sent_at timestamptz,
 smtp_message_id text, UNIQUE(ticket_id,revision)
);
CREATE OR REPLACE FUNCTION ticket_notify.observe(items jsonb) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE item jsonb; old ticket_notify.ticket_state%ROWTYPE; changes integer := 0; next_revision bigint;
BEGIN
 PERFORM pg_advisory_xact_lock(61303129);
 FOR item IN SELECT value FROM jsonb_array_elements(items) LOOP
  SELECT * INTO old FROM ticket_notify.ticket_state WHERE ticket_id=(item->>'ticket_id')::bigint FOR UPDATE;
  IF NOT FOUND THEN
   INSERT INTO ticket_notify.ticket_state(ticket_id,status_id,status_name,subject,requester_email,updated_on)
   VALUES((item->>'ticket_id')::bigint,(item->>'status_id')::bigint,item->>'status_name',item->>'subject',item->>'email',(item->>'updated_on')::timestamptz);
   CONTINUE;
  END IF;
  IF (item->>'updated_on')::timestamptz < old.updated_on THEN CONTINUE; END IF;
  next_revision := old.revision;
  IF old.status_id <> (item->>'status_id')::bigint THEN
   next_revision := old.revision + 1;
   INSERT INTO ticket_notify.notifications(ticket_id,revision,subject,previous_status,new_status,recipient,url,state,reason)
   VALUES(old.ticket_id,next_revision,item->>'subject',old.status_name,item->>'status_name',item->>'email',item->>'url',
    CASE WHEN (item->>'email_valid')::boolean THEN 'pending' ELSE 'suppressed' END,item->>'email_reason');
   changes := changes + 1;
  END IF;
  UPDATE ticket_notify.ticket_state SET status_id=(item->>'status_id')::bigint,status_name=item->>'status_name',subject=item->>'subject',
   requester_email=item->>'email',updated_on=(item->>'updated_on')::timestamptz,revision=next_revision,observed_at=now()
  WHERE ticket_id=old.ticket_id;
 END LOOP;
 RETURN changes;
END; $$;
REVOKE ALL ON FUNCTION ticket_notify.observe(jsonb) FROM PUBLIC;
