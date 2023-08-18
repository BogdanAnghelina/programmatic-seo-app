from sqlalchemy import create_engine, text
import os

db_connection_string = os.environ['db_connection_string']

engine = create_engine(
  db_connection_string,
  connect_args={
    "ssl": {
      "ssl_ca": "/etc/ssl/cert.pem"
    }
  })

with engine.connect() as conn:
    result = conn.execute(text("select * from templates"))
  
    result_dicts = []
    for row in result:
        result_dicts.append(row._asdict())

    print(result_dicts)