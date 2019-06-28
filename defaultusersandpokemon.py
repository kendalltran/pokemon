from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Pokemon, Base

engine = create_engine('sqlite:///pokemonCenter.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create default users
User1 = User(username="Ash Ketchum", useremail="ashketchum@gmail.com", picture="https://cdn.bulbagarden.net/upload/5/54/Ash_SM.png")
User2 = User(username="Brock", useremail="brock@gmail.com", picture="https://cdn.bulbagarden.net/upload/6/6a/Brock_SM.png")
User3 = User(username="Misty", useremail = "misty@gmail.com", picture="https://cdn.bulbagarden.net/upload/f/fb/Misty_SM.png")
session.add(User1)
session.add(User2)
session.add(User3)
session.commit()

# Create default pokemon
Pokemon1 = Pokemon(pokemonname="Pikachu", user=User1, picture="https://cdn.bulbagarden.net/upload/1/17/025Pikachu-Original.png", gender="Male")
Pokemon2 = Pokemon(pokemonname="Onyx", user=User2, picture="https://cdn.bulbagarden.net/upload/9/9a/095Onix.png", gender="Female")
Pokemon3 = Pokemon(pokemonname="Staryu", user=User3, picture="https://cdn.bulbagarden.net/upload/4/4f/120Staryu.png", gender="Female")
Pokemon4 = Pokemon(pokemonname="Charizard", user=User1, picture="https://cdn.bulbagarden.net/upload/7/7e/006Charizard.png", gender="Male")
session.add(Pokemon1)
session.add(Pokemon2)
session.add(Pokemon3)
session.add(Pokemon4)
session.commit()

print("added default users and pokemon!")
