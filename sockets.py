from flask_socketio import SocketIO, emit

socketio = SocketIO()

@socketio.on("connect")
def connect():
    print("Client Connected")