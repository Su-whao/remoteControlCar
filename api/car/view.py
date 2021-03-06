from flask import g, request, abort, jsonify
from . import car
from . import utils
from db import redis_cli, db
from auth import token_auth
from models import Car
from socket_io import socketio
from flask_socketio import emit


@socketio.on('connect')
@token_auth.login_required
def connect():
    emit('connect', {'status': 'success'})

@car.route('/regist', methods=['POST'])
def regist():
    car_id = request.form.get('id')
    ip_port = request.form.get("ip_port")
    car = Car.query.filter_by(id=car_id).first()
    if not car or not ip_port or not utils.judge_legal_ip(ip_port):
        abort(400)
    redis_cli.set('car:'+car_id, ip_port)
    redis_cli.expire('car:'+car_id, 60*60*2)

    # if the own is online
    user_id = car.own_id
    keys = redis_cli.keys(f"token:*:{user_id}:*")
    if keys:
        car_ip, car_port = ip_port.split(':')
        redis_cli.hmset(keys[0], mapping={'car_ip': car_ip, "car_port": car_port})
        new_key = keys[0][:52] + car_id
        redis_cli.rename(keys[0], new_key)
        socketio.emit('car_connected',
                        {'status':'success' ,'data': car_id})

    return jsonify({'status': 'success'})

@car.route('/', methods=['POST'])
@token_auth.login_required
def add():
    car = Car(own_id=g.user_id)
    db.session.add(car)
    db.session.commit()
    return jsonify({'status': 'success', 'data': car.id})


@car.route('/run', methods=['POST'])
@token_auth.login_required
def run():
    msg = None
    isbackward = request.form.get('backward')
    isreset = request.form.get("reset")
    if isbackward:
        msg = 'backward'
    else:
        msg = 'forward'
    if isreset:
        msg = 'reset_run'

    if g.car_ip and g.car_port:
        try:
            utils.send(g.car_ip, g.car_port, msg)
        except Exception:
            return jsonify({"status": "fail", "msg": "socket error"}),501
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail", "msg": 'Car`s ip or port is error.'})


@car.route("/turn", methods=['POST'])
@token_auth.login_required
def turn():
    '''转向：1 2 3 4 5
    '''
    angle = request.form.get('angle')
    msg = angle
    
    if g.car_ip and g.car_port:
        try:
            utils.send(g.car_ip, g.car_port, msg)
        except Exception:
            return jsonify({"status": "fail", "msg": "socket error"}),501
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail", "msg": 'Car`s ip or port is error.'})


@car.route("/gear", methods=['POST'])
@token_auth.login_required
def gear():
    msg = None
    isfast = request.form.get("fast")
    if isfast:
        msg = 'fast'
    else:
        msg = 'slow'

    if g.car_ip and g.car_port:
        try:
            utils.send(g.car_ip, g.car_port, msg)
        except Exception:
            return jsonify({"status": "fail", "msg": "socket error"}),501
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail", "msg": 'Car`s ip or port is error.'})


@car.route('/lock', methods=["POST"])
@token_auth.login_required
def lock():
    msg = None
    isopen = request.form.get('open')
    if isopen:
        msg = 'unlock'
    else:
        msg = 'lock'
    if g.car_ip and g.car_port:
        try:
            utils.send(g.car_ip, g.car_port, msg)
        except Exception:
            return jsonify({"status": "fail", "msg": "socket error"}),501
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail", "msg": 'Car`s ip or port is error.'})
