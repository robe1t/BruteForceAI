import sys, json
sys.path.insert(0, '.')
from app import create_app
app = create_app()
with app.app_context():
    from app.database.db import query_db
    rows = query_db('SELECT task_id, options, status FROM audit_tasks ORDER BY id DESC LIMIT 5')
    for r in rows:
        opts = json.loads(r['options']) if r['options'] else {}
        print(f"Task: {r['task_id']}, status={r['status']}")
        print(f"  username_dict_id: {opts.get('username_dict_id')}")
        print(f"  password_dict_id: {opts.get('password_dict_id')}")
        print(f"  username_list: {opts.get('username_list')}")
        print(f"  password_list: {opts.get('password_list')}")
        print()
