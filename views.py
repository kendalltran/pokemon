from flask import Flask, jsonify, request, render_template, redirect, url_for
# (A1) ^importing the Flask class.  this class, once made into an object, will
#   implement a WSGI application
# (D1) ^importing render_template allows us to utilize html files in the
#   'templates' folder
# (E1) ^importing request allows us to retrieve attributes of the GET or
#   POST request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Pokemon
import random
import string
from flask import session as login_session
import json
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import requests
from flask import make_response


app = Flask(__name__)
# (A2) ^create instance of Flask class.  use __name__ (generic) if single
#   module is used

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Pokemon Kantadlfajlkdto"


engine = create_engine('sqlite:///pokemonCenter.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
# (B1) ^connect to database and create database session via SQLAlchemy
#   built-in functions


@app.route("/login")
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return render_template('login.html', STATE = state)
    return render_template('login.html', STATE=state)
    # return "the current session state is %s" % login_session['state']


@app.route("/gconnect", methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the autorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        print("TOken's client ID doesn not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    def createUser(login_session):
        newUser = User(username=login_session['username'],
                       useremail=login_session['email'],
                       picture=login_session['picture'])
        session.add(newUser)
        session.commit()
        user = session.query(User).filter_by(
            useremail=login_session['email']).one()
        return user.userid

    def getUserInfo(user_id):
        user = session.query(User).filter_by(userid=user_id).one()
        return user

    def getUserID(email):
        try:
            user = session.query(User).filter_by(useremail=email).one()
            return user.userid
        except:
            return None

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    # flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = "https://accounts.google.com/o/oauth2/\n"
    "revoke?token=%s" % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        # response = make_response(json.dumps(
        #   'Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect('/')
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route("/kanto/<int:userid>/JSON/")
def viewUserJSON(userid):
    user = session.query(User).filter_by(userid=userid).one()
    return jsonify(user=user.serialize)
    # (C1) ^returns serialized date in JSON format (useful for other
    #   applications to retrieve/utilze this data)


@app.route("/kanto/<int:userid>/pokemons/JSON/")
def viewPokemonsJSON(userid):
    user = session.query(User).filter_by(userid=userid).one()
    pokemons = session.query(Pokemon).filter_by(user_id=userid).all()
    return jsonify(pokemons=[pokemon.serialize for pokemon in pokemons])


@app.route("/")
@app.route("/kanto/")
def viewKanto():
    users = session.query(User).all()
    if 'username' not in login_session:
        return render_template('publicusers.html', users=users)
    else:
        loggedInUserID = login_session['user_id']
        return render_template('users.html', users=users,
                               loggedInUserId=loggedInUserID)


@app.route("/kanto/add", methods=['GET', 'POST'])
def addUser():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newUser = User(username=request.form['name'],
                       useremail=request.form['email'],
                       picture=request.form['picture'])
        session.add(newUser)
        session.commit()
        return redirect(url_for('viewKanto'))
    else:
        return render_template('newUser.html')


@app.route("/kanto/<int:userid>/edit", methods=['GET', 'POST'])
def editUser(userid):
    if 'username' not in login_session:
        return redirect('/login')
    if userid != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to\
 edit this item. Please create your own item in order to edit.');}</script>\
    <body onload='myFunction()'>"
    user = session.query(User).filter_by(userid=userid).one()
    if request.method == 'POST':
        user.username = request.form['name']
        session.commit()
        return redirect(url_for('viewKanto'))
    else:
        return render_template('editUser.html', user=user)


@app.route("/kanto/<int:userid>/delete", methods=['GET', 'POST'])
def deleteUser(userid):
    if 'username' not in login_session:
        return redirect('/login')
    user = session.query(User).filter_by(userid=userid).one()
    if request.method == 'POST':
        session.delete(user)
        session.commit()
        return redirect(url_for('viewKanto'))
    else:
        return render_template('deleteUser.html', user=user)


@app.route("/kanto/<int:userid>/")
@app.route("/kanto/<int:userid>/pokemons/")
def viewPokemons(userid):
    user = session.query(User).filter_by(userid=userid).one()
    pokemons = session.query(Pokemon).filter_by(user_id=userid).all()
    if login_session['user_id'] != user.userid:
        return render_template('publicpokemons.html', user=user,
                               pokemons=pokemons)
    else:
        return render_template('pokemons.html', user=user,
                               pokemons=pokemons)


@app.route("/kanto/<int:userid>/pokemons/add", methods=['GET', 'POST'])
def addPokemon(userid):
    if 'username' not in login_session:
        return redirect('/login')
    if userid != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to\
 add. Please add Pokemon under own username.');}</script>\
    <body onload='myFunction()'>"
    user = session.query(User).filter_by(userid=userid).one()
    if request.method == 'POST':
        newPokemon = Pokemon(pokemonname=request.form['name'],
                             user_id=login_session['user_id'],
                             picture=request.form['picture'],
                             gender=request.form['gender'])
        session.add(newPokemon)
        session.commit()
        return redirect(url_for('viewPokemons', userid=userid))
    else:
        return render_template('newPokemon.html', user=user)


@app.route("/kanto/<int:userid>/pokemons/<int:pokemonid>/JSON/")
def viewPokemonJSON(userid, pokemonid):
    # (F1) ^ userid parameter not actually needed in logic.  only necessary
    #   to keep the URI valid
    pokemon = session.query(Pokemon).filter_by(pokemonid=pokemonid).one()
    return jsonify(pokemon=pokemon.serialize)


@app.route("/kanto/<int:userid>/pokemons/<int:pokemonid>/edit",
           methods=['GET', 'POST'])
def editPokemon(userid, pokemonid):
    # user = session.query(User).filter_by(userid = userid).one()
    if 'username' not in login_session:
        return redirect('/login')
    if userid != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to\
 edit this item. Please create your own item in order to edit.');}</script>\
    <body onload='myFunction()'>"
    pokemon = session.query(Pokemon).filter_by(user_id=userid,
                                               pokemonid=pokemonid).one()
    if request.method == 'POST':
        pokemon.pokemonname = request.form['name']
        pokemon.gender = request.form['gender']
        session.commit()
        return redirect(url_for('viewPokemons', userid=userid))
    else:
        return render_template('editPokemon.html', pokemon=pokemon)


@app.route("/kanto/<int:userid>/pokemons/<int:pokemonid>/delete",
           methods=['GET', 'POST'])
def deletePokemon(userid, pokemonid):
    if 'username' not in login_session:
        return redirect('/login')
    if userid != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to\
 delete this item. Please create your own item in order to delete.');}</script>\
    <body onload='myFunction()'>"
    pokemon = session.query(Pokemon).filter_by(user_id=userid,
                                               pokemonid=pokemonid).one()
    if request.method == 'POST':
        session.delete(pokemon)
        session.commit()
        return redirect(url_for('viewPokemons', userid=userid))
    else:
        return render_template('deletePokemon.html', pokemon=pokemon)

print("Welcome to Kanto (server side)")

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    # ^????
    app.debug = True
    app.run(host='0.0.0.0', port=7000)
# (A3) ^runs instance on dev server at specified port


# supporting links & top-level notes:
    # http://flask.pocoo.org/docs/1.0/api/#flask.Flask
    # this is server side code.  all client side code is .html
