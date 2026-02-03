from flask import Flask , render_template, request, url_for, session, redirect
from flask_socketio import SocketIO, join_room, leave_room,send
import random
from string import ascii_uppercase
 
app = Flask(__name__)

app.config['SECRET_KEY'] = "Gururaj@18091hhujahscuyqwebnacs8y823cwsdcb672nw3bsxccunwsd7n23w"
socketio = SocketIO(app, manage_session="eventlet")


rooms = {}

def generate_unique_code(lenth):
    while True:
        code = ""
        for _ in range(lenth):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
              break
    return code


@app.route("/", methods = ['GET','POST'])
def homepage():
    session.clear()
    return render_template("index.html")

@app.route('/create', methods=['POST'])
def create():
    name = request.form.get('name')
    chat_name = request.form.get('chat_name')
    password = request.form.get('password')

    if not name or not chat_name or not password:
        return render_template(
            'index.html',
            error="Please fill all the fields",
            name=name,
            chat_name=chat_name
        )

    code = generate_unique_code(4)

    rooms[code] = {
        "members": 0,
        "password": password,
        "chat_name": chat_name,
        "messages": []
    }

    session['name'] = name
    session['chat_name'] = chat_name
    session['chat_code'] = code
    session['show_password_once'] = True
    session['temp_password'] = password 
    return redirect(url_for('room_created'))

    

@app.route('/join', methods = ['GET','POST'])
def join():
    
    if request.method == "POST":
        name = request.form.get('name')
        chat_code = request.form.get('chat_code')
        password = request.form.get('password')
        if not name or not chat_code or not password:
            return render_template('index.html', error = "Please fill all the feilds",name=name,chat_code=chat_code,password=password)
        if chat_code not in rooms:
            return render_template(
                'index.html',
                error="Room does not exist",
                name=name,
                chat_code=chat_code,
                password=password
                     )

        elif password != rooms[chat_code]['password']:
              return render_template(
                'index.html',
                error="Wrong password",
                name=name,
                chat_code=chat_code,
                password=password
           )

        else:
            session['chat_name'] = rooms[chat_code]['chat_name']
            session['chat_code'] = chat_code
            session['name'] = name
            session['password'] = password
            members = rooms[chat_code]['members']
            return redirect(url_for('chat'))
         
    return render_template('index.html')

@app.route('/room-created')
def room_created():
    if not session.get('show_password_once'):
        return redirect(url_for('chat'))

    return render_template(
        'room_created.html',
        chat_name=session['chat_name'],
        chat_code=session['chat_code'],
        password=session['temp_password']
    )

    
@app.after_request
def clear_password(response):
    if request.endpoint == 'room_created':
        session.pop('temp_password', None)
        session.pop('show_password_once', None)
    return response



@app.route('/chat')
def chat():
    chat_code = session.get('chat_code')
    chat_name = session.get('chat_name')
    name = session.get('name')

    if not chat_code or not chat_name or not name:
        return redirect(url_for('homepage'))

    if chat_code not in rooms:
        return redirect(url_for('homepage'))

    members = rooms[chat_code]['members']

    return render_template(
        'chat.html',
        code=chat_code,
        chat_name=chat_name,
        name=name,
        memebers=members
    )





@socketio.on("connect")
def connect(auth):
    room = session.get('chat_code')
    name = session.get('name')
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name":name, "message":"has entered the room"}, to=room)
    rooms[room]['members'] += 1
    print(f"{name} joined room")
    
@socketio.on('disconnect')
def disconnect():
    room = session.get('chat_code')
    name = session.get('name')
    if room:
        leave_room(room)

    
    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]
    send ({"name":name,"message":"has left the room"}, to=room)
    print(f"{name} has left the room {room}")
    
    
@socketio.on('message')
def message(data):
    room = session.get('chat_code')
    if room not in rooms:
        return
    
    content = {
        "name":session.get('name'),
        "message": data['data']
    }
    send(content, to=room)
    rooms[room]['messages'].append(content)
    print(f"{session.get('name')} said: {data['data']}")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
