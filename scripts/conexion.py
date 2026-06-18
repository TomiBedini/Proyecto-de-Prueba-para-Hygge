import os
from dotenv import load_dotenv
import psycopg2
     
load_dotenv()
     
DATABASE_URL = os.getenv("DATABASE_URL")
  
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
  
cursor.execute("SELECT version();")
resultado = cursor.fetchone()
print("Conexión exitosa:", resultado)
  
cursor.close()
conn.close()