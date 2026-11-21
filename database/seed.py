"""Security/database owner: future reproducible synthetic SQLite seeding.
Current fixture records live in MockRepository; no real healthcare data.
"""
import argparse
from database.database import connect, initialize_database

CUSTOMERS = [(f'C{i:03}', f'Demo Customer {i:02}') for i in range(1, 26)]
POLICIES = [(f'P{i:03}', f'C{i:03}', 'Demo Basic' if i % 2 else 'Demo Plus',
             'active', f'Synthetic policy P{i:03}: ' + ('Demo Basic' if i % 2 else 'Demo Plus') + ', active.')
            for i in range(1, 26)]
CLAIMS = [(f'CL{i:03}', f'C{i:03}',
           'fictional checkup' if i % 2 else 'fictional consultation',
           'pending' if i % 2 else 'approved', 4000 if i % 2 else 6000)
           for i in range(1, 26)]

def seed_database(db_path):
    initialize_database(db_path)
    with connect(db_path) as connection:
        connection.executemany('INSERT OR IGNORE INTO customers VALUES (?, ?)', CUSTOMERS)
        connection.executemany('INSERT OR IGNORE INTO policies VALUES (?, ?, ?, ?, ?)', POLICIES)
        connection.executemany('INSERT OR IGNORE INTO claims VALUES (?, ?, ?, ?, ?)', CLAIMS)
    return {'customers': len(CUSTOMERS), 'policies': len(POLICIES), 'claims': len(CLAIMS)}

def main():
    parser = argparse.ArgumentParser(description='Seed fictional CometCare SQLite records; safe to repeat.')
    parser.add_argument('--db', required=True, help='SQLite file path (parent directory mst exist)')
    args = parser.parse_args()
    print(f'Seed fixtures ensured at {args.db}: {seed_database(args.db)}')

if __name__ == '__main__':
    main()