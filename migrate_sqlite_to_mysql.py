import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker

def migrate_data():
    # 1. Setup connections
    sqlite_url = "sqlite:///backend/instance/dev.db"
    # Read MySQL URL from env variable or use the one we just configured
    mysql_url = os.environ.get(
        "DATABASE_URL", 
        "mysql+pymysql://Vincent:Admin%401234@localhost:3306/education_website_stable"
    )

    print(f"Connecting to SQLite: {sqlite_url}")
    print(f"Connecting to MySQL: {mysql_url}")

    sqlite_engine = create_engine(sqlite_url)
    mysql_engine = create_engine(mysql_url)

    # 2. Reflect tables from SQLite
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)
    
    mysql_meta = MetaData()
    mysql_meta.reflect(bind=mysql_engine)

    # 3. Copy data table by table
    with mysql_engine.connect() as mysql_conn:
        # Disable foreign key checks temporarily so order of insertion doesn't matter
        mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        
        with sqlite_engine.connect() as sqlite_conn:
            for table_name in sqlite_meta.tables:
                print(f"Migrating table: {table_name}...")
                
                sqlite_table = sqlite_meta.tables[table_name]
                mysql_table = mysql_meta.tables[table_name]
                
                # Fetch all rows from SQLite
                result = sqlite_conn.execute(sqlite_table.select())
                rows = result.fetchall()
                
                if not rows:
                    print(f"  - Table {table_name} is empty, skipping.")
                    continue
                
                # Convert rows to list of dicts for bulk insert
                keys = result.keys()
                data_to_insert = [dict(zip(keys, row)) for row in rows]
                
                # Clear existing data in MySQL table to avoid conflicts
                mysql_conn.execute(mysql_table.delete())
                
                # Insert data into MySQL
                mysql_conn.execute(mysql_table.insert(), data_to_insert)
                print(f"  - Inserted {len(data_to_insert)} rows into {table_name}.")
                
        # Re-enable foreign key checks
        mysql_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        mysql_conn.commit()

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_data()
