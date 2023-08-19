from sqlalchemy import create_engine, text, Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

db_connection_string = os.environ['db_connection_string']

engine = create_engine(
    db_connection_string,
    connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem"
        }
    }
)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Template(Base):
    __tablename__ = 'templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(200), nullable=False)
    template_content = Column(Text, nullable=False)
    template_variables = Column(Text, nullable=True)
    draft = Column(Boolean, default=True)
    user_id = Column(String(50), nullable=False)