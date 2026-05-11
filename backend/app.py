from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from models import db, Task
from email_service import send_smtp, check_imap, check_pop3
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'todo-secret-lab5')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@db:5432/tododb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Инициализация SocketIO с поддержкой CORS
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=False,
    engineio_logger=False
)

with app.app_context():
    db.create_all()


# ── WebSocket события ────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    """Новый клиент подключился — отправляем ему актуальный список задач."""
    print(f'[WS] Клиент подключился: {request.sid}')
    with app.app_context():
        tasks = Task.query.order_by(Task.id.desc()).all()
        emit('init', [t.to_dict() for t in tasks])


@socketio.on('disconnect')
def on_disconnect():
    print(f'[WS] Клиент отключился: {request.sid}')


# ── CRUD REST API ─────────────────────────────────────────────────────────────

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.order_by(Task.id.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'pending')
    )
    db.session.add(task)
    db.session.commit()

    task_dict = task.to_dict()
    # Оповещаем всех подключённых клиентов о новой задаче
    socketio.emit('task_created', task_dict)
    return jsonify(task_dict), 201


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']

    db.session.commit()

    task_dict = task.to_dict()
    # Оповещаем всех подключённых клиентов об изменении
    socketio.emit('task_updated', task_dict)
    return jsonify(task_dict)


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()

    # Оповещаем всех подключённых клиентов об удалении
    socketio.emit('task_deleted', {'id': task_id})
    return jsonify({'message': 'Task deleted'})


# ── EMAIL ─────────────────────────────────────────────────────────────────────

@app.route('/email/send', methods=['POST'])
def send_email():
    data = request.get_json()
    to_email = data.get('to')
    subject = data.get('subject', 'Todo List Report')
    body = data.get('body', '')
    if not to_email:
        return jsonify({'error': 'Recipient email required'}), 400
    result = send_smtp(to_email, subject, body)
    return jsonify(result)


@app.route('/email/imap', methods=['GET'])
def imap_inbox():
    return jsonify(check_imap())


@app.route('/email/pop3', methods=['GET'])
def pop3_inbox():
    return jsonify(check_pop3())


# ── Health check для CI/CD ────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'todo-backend'}), 200


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
