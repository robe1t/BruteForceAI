import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()
with app.app_context():
    from app.database.db import query_db
    rows = query_db('SELECT * FROM dictionaries')
    print(f'Dictionaries count: {len(rows)}')
    for r in rows:
        print(f'  id={r["id"]}, name={r["name"]}, type={r["type"]}, count={r["count"]}')
    if len(rows) == 0:
        print('No dictionaries found! Upload dictionaries first.')
