#! /usr/bin/env python3
import re
import eventlet
import ssl
from flask import Flask, request
import datetime
import os
import subprocess

from flask_socketio import SocketIO, send

d = datetime.datetime.now()
today = "{}:{}:{}".format(d.hour, d.minute, d.second)

check_size = os.stat("users.csv")
#Checks that users.csv log is less than 100kb
if int(re.search(r"(?<=st_size=)\d+", str(check_size)).group(0)) > 100000:
    print("Larger than 100kb")
    os.remove("users.csv")
    subprocess.check_output(["touch","users.csv"])
    subprocess.check_output(["service","chat_room","restart"])
else:
    print("Less than 100kb")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simplepassword'
socketio = SocketIO(app, cors_allowed_origins="*")

def ident_user(sid, user=''):
    with open('users.csv', 'a') as user_id:
        user_id.write("{}\n".format({sid: user}))
        user_id.close()

def retrieve_user(sid):
    with open('users.csv', 'r') as file:
        reader = file.readlines()
        for i in reader:
            if sid in i:
                file.close()
                return re.search(r"(?<=': ').*?(?=')".format(sid), i).group(0)

notAllow = ['"','\'','[',']','{','}','python','import','script','<','>']

@socketio.on('message')
def handleMessage(msg, user=''):
        if "has connected!" in msg:
                ident_user(request.sid, dict(user)['selector'])
        try:
            user = dict(user)['selector']
        except KeyError:
            pass
        if any(x in msg for x in notAllow):
                send("{}: ".format(user) + "Forbidden characters in msg. <p>prxIP: {}</p>".format(request.user_agent, request.remote_addr), broadcast=True)
        else:
                send('{}: '.format(user) + "{}<p>{}, prxIP: {}</p>".format(msg,request.user_agent, request.remote_addr), broadcast=True)

@socketio.on('connect')
def onConnect():
        pass


@socketio.on('disconnect')
def onDisconnect():
    send("{} has disconnected!".format(retrieve_user(request.sid)), broadcast=True)


if __name__ == '__main__':
        socketio.run(
        app,
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=False
        )