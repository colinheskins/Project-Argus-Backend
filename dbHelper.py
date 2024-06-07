import os
import psycopg2
import json
from psycopg2 import sql
from psycopg2.extras import Json, DictCursor
from datetime import datetime, timedelta


def start():
  DATABASE_URL = os.environ["DATABASE_URL"]
  conn = psycopg2.connect(DATABASE_URL)
  cur = cur = conn.cursor(cursor_factory=DictCursor)
  return cur, conn


def delete_user(STEAMID, db_name1="northmen_us"):
  cur, conn = start()
  cur.execute(
      f"""
      DELETE FROM {db_name1}
      WHERE steam_id = %s
      """, (STEAMID, ))
  conn.commit()
  cur.close()
  conn.close()


def get_table(table_name="northmen_us"):
  cur, conn = start()
  cur.execute(f"SELECT * FROM {table_name}")
  data = cur.fetchall()
  cur.close()
  conn.close()
  return data


def get_entries_between_dates(start_date, db_name):
  table_name = db_name
  cur, conn = start()

  # Format current date
  start_date_converted = datetime.strptime(start_date,
                                           '%d/%m/%Y').strftime('%Y-%m-%d')

  # Get the current date in 'yyyy-mm-dd' format
  end_date = datetime.now().strftime('%Y-%m-%d')

  get_entries_query = f"""
      SELECT * FROM {table_name}
      WHERE TO_DATE(date, 'DD/MM/YYYY') BETWEEN %s AND %s
  """

  # Execute the SQL statement to get the entries
  cur.execute(get_entries_query, (start_date_converted, end_date))
  entries = cur.fetchall()

  # Close cursor and connection
  cur.close()
  conn.close()

  result = [] 
  for entry in entries:
    for each in entry[-1]:
      if each["prediction"] == "0":
        result.append(each)
        break

  return result

def getBulkData(steam_ids, db_name="northmen_us"):
  cur, conn = start()
  query = sql.SQL(f"SELECT * FROM {db_name} WHERE" + " steam_id IN ({})").format(
    sql.SQL(',').join(map(sql.Literal, steam_ids))
  )

  # Execute query
  with conn.cursor() as cursor:
    cursor.execute(query)
    result = cursor.fetchall()

  # Close connection
  conn.close()

  return result



def search_for_user(STEAMID, db_name1):
  cur, conn = start()
  cur.execute(
      f"""
    SELECT data FROM {db_name1}
    WHERE steam_id = %s
    """, (STEAMID, ))
  row = cur.fetchone()
  cur.close()
  conn.close()
  if row:
    return row[0]
  else:
    return None


def add_user(data, table_name):
  cur, conn = start()
  dictArray = search_for_user(data["steam_id"], db_name1=table_name)
  if dictArray is None:
    dictArray = [data]

  else:
    dictArray.append(data)
    delete_user(data["steam_id"], db_name1=table_name)
  cur.execute(
      f"""
    INSERT INTO {table_name} (steam_id, date, data)
    VALUES (%s, %s, %s)
    """, (data["steam_id"], data["date"], json.dumps(dictArray)))

  # Commit the transaction
  conn.commit()
  cur.close()
  conn.close()


def create_table(table_name):
  cur, conn = start()
  create_table_query = f"""
      CREATE TABLE IF NOT EXISTS {table_name} (
          steam_id VARCHAR(17) PRIMARY KEY,
          date VARCHAR(10),
          data JSONB
      )
  """
  # Execute the SQL statement to create the table
  cur.execute(create_table_query)

  # Commit the transaction
  conn.commit()

  # Close cursor and connection
  cur.close()
  conn.close()


def delete_table(table_name):
  cur, conn = start()
  create_table_query = f"""
      DROP TABLE IF EXISTS {table_name}
  """

  # Execute the SQL statement to create the table
  cur.execute(create_table_query)

  # Commit the transaction
  conn.commit()

  # Close cursor and connection
  cur.close()
  conn.close()
