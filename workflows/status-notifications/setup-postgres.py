import json,secrets
from pathlib import Path
import psycopg
from psycopg import sql
c={}
for line in Path('.env').read_text(encoding='utf-8-sig').splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);c[k]=v.strip().strip("'\"")
p=Path('.secrets/status-notifications-postgres.json')
cred=json.loads(p.read_text()) if p.exists() else dict(host='postgres',port=5432,database='n8n',user='mquito_ticket_notify',password=secrets.token_hex(32),ssl='disable',sshTunnel=False)
p.write_text(json.dumps(cred))
with psycopg.connect(host=c['SERVER_HOST'],port=int(c.get('POSTGRES_PORT',5432)),dbname='n8n',user=c.get('POSTGRES_USER','postgres'),password=c['POSTGRES_PASSWORD'],connect_timeout=10) as db:
 db.execute(Path('workflows/status-notifications/schema.sql').read_text(encoding='utf-8-sig'))
 if not db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',(cred['user'],)).fetchone():
  db.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Identifier(cred['user']),sql.Literal(cred['password'])))
 role=sql.Identifier(cred['user'])
 for q in ['GRANT CONNECT ON DATABASE n8n TO {}','GRANT USAGE ON SCHEMA ticket_notify TO {}','GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA ticket_notify TO {}','GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA ticket_notify TO {}','GRANT EXECUTE ON FUNCTION ticket_notify.observe(jsonb) TO {}',"ALTER ROLE {} SET statement_timeout='15s'"]:
  db.execute(sql.SQL(q).format(role))
print('Esquema de seguimiento y usuario dedicado preparados.')
