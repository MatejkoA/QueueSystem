from flask import Flask, render_template, session, redirect, url_for
from uuid import uuid4
from datetime import datetime, timedelta
import pytz

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "ThisJustHasToBeARandomStringOfCharacters"

placement = 0
placementDict = {}
wait_time = 3
recent_joins = 0

@app.before_request
def reset_placement():
    global placement
    if placement > 0:
        # reset placement to zero every day at midnight
        now = datetime.now(pytz.utc)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        if now >= midnight:
            placement = 0

@app.before_request
def update_recent_joins():
    global recent_joins
    local_tz = pytz.timezone("Europe/Copenhagen")
    now = datetime.now(local_tz)
    join_time = session.get('join_time', None)
    if join_time and now < join_time + timedelta(minutes=5):
        recent_joins += 1
    else:
        recent_joins = 0
    session['join_time'] = now

def setQ():
    global placement
    global placementDict
    global wait_time
    session['id'] = str(uuid4())
    placement += 1
    placementDict[session['id']] = placement
    session['qNumber'] = placementDict[session['id']]

    now = datetime.now(pytz.utc)
    current_time = now.strftime("%H:%M:%S")
    session['join_time'] = now

    local_tz = pytz.timezone("Europe/Copenhagen")
    join_time = session['join_time'].astimezone(local_tz)
    if recent_joins > 5 and (now - timedelta(minutes=10)) < join_time:
        wait_time += 5 # increase wait time by 5 minutes

    serv_time = now + timedelta(minutes=wait_time)
    serve_time = serv_time.strftime("%H:%M:%S")

    session['join'] = current_time
    session['serv'] = serve_time


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/join')
def join():
    global wait_time
    setQ()
    return redirect(url_for('queue'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/queue')
def queue():
    if 'id' not in session:
        return redirect(url_for('join'))

    num = session['qNumber']
    userId = session['id']
    joinTime = session['join']
    servTime = session['serv']

    return render_template("queue.html", num=num, id=userId, tim=joinTime, servTim=servTime)


@app.route('/leave')
def leave():
    global placement
    if session.get('id'):
        sessID = session['id']
        placementDict.pop(sessID)
        placement -= 1 # decrement placement count
        session['id'] = None
        session['qNumber'] = None
        session['join'] = None
        session['serv'] = None

    return render_template("leave.html")


if __name__ == '__main__':
    app.run()
