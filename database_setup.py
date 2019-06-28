from sqlalchemy import Column,Integer,String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    userid = Column(Integer, primary_key=True)
    username = Column(String(32), nullable=False)
    useremail = Column(String(32), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'userid': self.userid,
            'username': self.username
            }

class Pokemon(Base):
    __tablename__ = 'pokemon'
    pokemonid = Column(Integer, primary_key=True)
    pokemonname = Column(String(32), nullable=False)
    user_id = Column(Integer, ForeignKey('user.userid'))
    user = relationship(User)
    picture = Column(String(250))
    gender = Column(String(20))


    @property
    def serialize(self):
        "Return object data in easily serializable format"
        return {
            'pokemonid': self.pokemonid,
            'pokemonname': self.pokemonname,
            'gender': self.gender
            }

engine = create_engine('sqlite:///pokemonCenter.db')
Base.metadata.create_all(engine)
