"""Train TF-IDF + multinomial logistic regression and export portable coefficients.

Demo rows are synthetic. No accuracy claim is made from training examples.
Usage: python classifier/train.py [--data path.csv --source real --version v2]
"""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent

def normalize(text):
    text = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=ROOT / 'demo.csv')
    p.add_argument('--source', choices=['synthetic', 'real'], default='synthetic')
    p.add_argument('--version', default='demo-v1')
    p.add_argument('--output', type=Path, default=ROOT / 'model.json')
    args = p.parse_args()
    if args.source == 'real' and args.data.resolve() == (ROOT / 'demo.csv').resolve():
        p.error('demo.csv es sintético; no puede etiquetarse como real')
    with args.data.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    classes = ['accesos', 'aplicaciones', 'infraestructura', 'otros']
    if not rows or any(not r.get('categoria') in classes or not r.get('cuerpo', '').strip() for r in rows):
        p.error('CSV requiere asunto,cuerpo,categoria y cuerpo no vacío; revisar categorías')
    if set(r['categoria'] for r in rows) != set(classes):
        p.error('Incluir ejemplos de las cuatro categorías')
    texts = [r.get('asunto', '')[:255] + '\n' + r['cuerpo'][:16000] for r in rows]
    # ASCII tokens after accent normalization: exactly reproduced in the n8n node.
    vec = TfidfVectorizer(preprocessor=normalize, token_pattern=r'[a-z0-9]{2,}', ngram_range=(1, 2))
    x = vec.fit_transform(texts)
    # The current corpus is imbalanced; keep minority categories represented.
    lr = LogisticRegression(C=1.0, max_iter=1000, solver='lbfgs', random_state=42, class_weight='balanced')
    lr.fit(x, [r['categoria'] for r in rows])
    model = dict(version=args.version, source=args.source, technique='TF-IDF + logistic regression',
                 sklearn_version=sklearn.__version__, samples=len(rows), class_weight='balanced',
                 class_counts={c: sum(r['categoria'] == c for r in rows) for c in classes},
                 dataset_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                 classes=lr.classes_.tolist(), vocabulary={k: int(v) for k, v in vec.vocabulary_.items()},
                 idf=vec.idf_.tolist(), weights=lr.coef_.tolist(), intercept=lr.intercept_.tolist(),
                 evaluated_on_held_out_data=False)
    args.output.write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    # Synthetic probes verify JS/Python numerical parity, not predictive quality.
    probes = ['Cuenta bloqueada\nNo puedo iniciar sesión con mi contraseña',
              'Impresora\nLa red no funciona', 'Error\nEl programa falla al guardar',
              'Consulta\nHorario de capacitación', '', '🦊 xyzabc', 'ACCESO\ncontraseña contraseña']
    fixture = [dict(text=t, probabilities=lr.predict_proba(vec.transform([t]))[0].tolist()) for t in probes]
    args.output.with_name('parity-fixtures.json').write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
    print(f'Modelo {args.version}: {len(rows)} ejemplos {args.source}; sin evaluación independiente.')

if __name__ == '__main__':
    main()
