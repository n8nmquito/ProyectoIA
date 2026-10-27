"""Create isolated ML tables and upload a versioned model, using admin .env locally.
No model coefficients or passwords are printed. Re-running preserves the reader password.
"""
import csv
import json
import secrets
from pathlib import Path
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parent.parent

def main():
    config = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            config[k] = v.strip().strip("'\"")
    private = ROOT / '.secrets' / 'ml-postgres.json'
    credential = json.loads(private.read_text()) if private.exists() else {
        'host': 'postgres', 'port': 5432, 'database': 'n8n',
        'user': 'mquito_ml_reader', 'password': secrets.token_hex(32),
        'ssl': 'disable', 'maxConnections': 5, 'sshTunnel': False,
    }
    model = json.loads((ROOT / 'classifier/model.json').read_text(encoding='utf-8'))
    if model['source'] != 'synthetic':
        raise ValueError('Este importador de demostración solo carga model.json sintético y demo.csv.')
    with (ROOT / 'classifier/demo.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    import hashlib
    if hashlib.sha256((ROOT / 'classifier/demo.csv').read_bytes()).hexdigest() != model['dataset_sha256']:
        raise ValueError('El CSV no coincide con el conjunto de entrenamiento del modelo')
    # Save before transaction: a retry can reuse the generated password if a network reply is lost.
    existed = private.exists()
    with psycopg.connect(host=config['SERVER_HOST'], port=int(config.get('POSTGRES_PORT', 5432)),
                          dbname=credential['database'], user=config.get('POSTGRES_USER', 'postgres'),
                          password=config['POSTGRES_PASSWORD'], connect_timeout=10) as db:
        role_exists = db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (credential['user'],)).fetchone()
        if role_exists and not existed:
            raise ValueError('El usuario ML ya existe, pero falta su credencial local; no se modificó.')
        private.write_text(json.dumps(credential), encoding='utf-8')
        if not role_exists:
            db.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}').format(
                sql.Identifier(credential['user']), sql.Literal(credential['password'])))
        db.execute('CREATE SCHEMA IF NOT EXISTS ml')
        db.execute('''CREATE TABLE IF NOT EXISTS ml.modelos (
            version text PRIMARY KEY,
            artifact jsonb NOT NULL CHECK (jsonb_typeof(artifact)='object'),
            activo boolean NOT NULL DEFAULT false,
            creado_en timestamptz NOT NULL DEFAULT now()
        )''')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS ml_un_modelo_activo ON ml.modelos (activo) WHERE activo')
        db.execute('''CREATE TABLE IF NOT EXISTS ml.correos_entrenamiento (
            modelo_version text NOT NULL REFERENCES ml.modelos(version),
            ejemplo integer NOT NULL,
            asunto text NOT NULL,
            cuerpo text NOT NULL,
            categoria text NOT NULL CHECK (categoria IN ('accesos','aplicaciones','infraestructura','otros')),
            origen text NOT NULL,
            PRIMARY KEY (modelo_version, ejemplo)
        )''')
        prior = db.execute('SELECT artifact FROM ml.modelos WHERE version=%s', (model['version'],)).fetchone()
        if prior and prior[0] != model:
            raise ValueError('La versión ya existe con otro contenido: usar una versión nueva.')
        db.execute('UPDATE ml.modelos SET activo=false WHERE activo AND version<>%s', (model['version'],))
        db.execute('''INSERT INTO ml.modelos(version,artifact,activo) VALUES (%s,%s,true)
                      ON CONFLICT(version) DO UPDATE SET activo=true''', (model['version'], Jsonb(model)))
        for i, row in enumerate(rows):
            db.execute('''INSERT INTO ml.correos_entrenamiento VALUES (%s,%s,%s,%s,%s,%s)
                          ON CONFLICT (modelo_version,ejemplo) DO NOTHING''',
                       (model['version'],i+1,row['asunto'],row['cuerpo'],row['categoria'],model['source']))
        reader = sql.Identifier(credential['user'])
        db.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(credential['database']), reader))
        db.execute(sql.SQL('GRANT USAGE ON SCHEMA ml TO {}').format(reader))
        db.execute(sql.SQL('GRANT SELECT ON ml.modelos TO {}').format(reader))
        db.execute(sql.SQL("ALTER ROLE {} SET statement_timeout = '5s'").format(reader))
        db.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(reader))
    # Verify the restricted account through the public mapping, not the Docker hostname.
    with psycopg.connect(host=config['SERVER_HOST'], port=int(config.get('POSTGRES_PORT',5432)),
                          dbname=credential['database'], user=credential['user'], password=credential['password'],
                          connect_timeout=10) as db:
        assert db.execute('SELECT artifact FROM ml.modelos WHERE activo').fetchone()[0] == model
        assert not db.execute("SELECT has_table_privilege(current_user,'ml.modelos','UPDATE')").fetchone()[0]
        assert not db.execute("SELECT has_table_privilege(current_user,'ml.correos_entrenamiento','SELECT')").fetchone()[0]
    print(f'PostgreSQL: modelo {model["version"]}, {len(rows)} correos sintéticos; acceso de lectura verificado.')

if __name__ == '__main__':
    main()
