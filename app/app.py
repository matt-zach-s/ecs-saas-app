from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import socket
from models import db, MealTask

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thanksgiving.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables and sample data
with app.app_context():
    db.create_all()

    # Add sample data if database is empty
    if MealTask.query.count() == 0:
        sample_tasks = [
            MealTask(
                name="Roast Turkey",
                description="24-pound turkey with herb butter",
                category="main",
                status="planned",
                priority=1,
                start_time="11:00 AM",
                duration_minutes=240,
                assigned_to="Chef",
                ingredients="turkey,butter,herbs,salt,pepper,garlic"
            ),
            MealTask(
                name="Mashed Potatoes",
                description="Creamy mashed potatoes with butter and cream",
                category="side",
                status="planned",
                priority=2,
                start_time="2:00 PM",
                duration_minutes=45,
                assigned_to="Sous Chef",
                ingredients="potatoes,butter,cream,salt,garlic"
            ),
            MealTask(
                name="Green Bean Casserole",
                description="Classic green bean casserole with crispy onions",
                category="side",
                status="planned",
                priority=3,
                start_time="2:30 PM",
                duration_minutes=60,
                assigned_to="Helper 1",
                ingredients="green beans,mushroom soup,milk,crispy onions"
            ),
            MealTask(
                name="Cranberry Sauce",
                description="Homemade cranberry sauce with orange zest",
                category="side",
                status="in_progress",
                priority=4,
                start_time="1:00 PM",
                duration_minutes=30,
                assigned_to="Helper 2",
                ingredients="cranberries,sugar,orange,water"
            ),
            MealTask(
                name="Pumpkin Pie",
                description="Traditional pumpkin pie with whipped cream",
                category="dessert",
                status="completed",
                priority=5,
                start_time="9:00 AM",
                duration_minutes=90,
                assigned_to="Baker",
                ingredients="pumpkin,eggs,cream,sugar,cinnamon,pie crust"
            ),
            MealTask(
                name="Stuffing",
                description="Savory bread stuffing with herbs",
                category="side",
                status="planned",
                priority=2,
                start_time="1:30 PM",
                duration_minutes=60,
                assigned_to="Chef",
                ingredients="bread,celery,onion,butter,herbs,chicken broth"
            ),
            MealTask(
                name="Gravy",
                description="Turkey gravy from pan drippings",
                category="side",
                status="planned",
                priority=1,
                start_time="3:15 PM",
                duration_minutes=15,
                assigned_to="Chef",
                ingredients="turkey drippings,flour,chicken broth,salt,pepper"
            ),
            MealTask(
                name="Dinner Rolls",
                description="Soft and buttery dinner rolls",
                category="side",
                status="in_progress",
                priority=3,
                start_time="2:00 PM",
                duration_minutes=120,
                assigned_to="Baker",
                ingredients="flour,yeast,milk,butter,sugar,salt,eggs"
            ),
            MealTask(
                name="Caesar Salad",
                description="Fresh Caesar salad with homemade dressing",
                category="appetizer",
                status="planned",
                priority=4,
                start_time="3:00 PM",
                duration_minutes=20,
                assigned_to="Helper 1",
                ingredients="romaine lettuce,parmesan,croutons,caesar dressing,lemon"
            ),
            MealTask(
                name="Pecan Pie",
                description="Sweet pecan pie with vanilla ice cream",
                category="dessert",
                status="completed",
                priority=5,
                start_time="9:30 AM",
                duration_minutes=75,
                assigned_to="Baker",
                ingredients="pecans,corn syrup,eggs,butter,sugar,vanilla,pie crust"
            )
        ]
        db.session.add_all(sample_tasks)
        db.session.commit()

@app.route('/')
def index():
    """Serve the main frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/info')
def info():
    """API info endpoint"""
    return jsonify({
        'message': 'Thanksgiving Meal Planner API',
        'hostname': socket.gethostname(),
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

# Task endpoints
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all meal tasks"""
    tasks = MealTask.query.order_by(MealTask.priority).all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    task = MealTask.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    task = MealTask(
        name=data.get('name'),
        description=data.get('description'),
        category=data.get('category'),
        status=data.get('status', 'planned'),
        priority=data.get('priority', 1),
        start_time=data.get('start_time'),
        duration_minutes=data.get('duration_minutes'),
        assigned_to=data.get('assigned_to'),
        ingredients=','.join(data.get('ingredients', []))
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    task = MealTask.query.get_or_404(task_id)
    data = request.json

    if 'name' in data:
        task.name = data['name']
    if 'description' in data:
        task.description = data['description']
    if 'category' in data:
        task.category = data['category']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'start_time' in data:
        task.start_time = data['start_time']
    if 'duration_minutes' in data:
        task.duration_minutes = data['duration_minutes']
    if 'assigned_to' in data:
        task.assigned_to = data['assigned_to']
    if 'ingredients' in data:
        task.ingredients = ','.join(data['ingredients'])

    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = MealTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the meal planning"""
    total_tasks = MealTask.query.count()
    completed = MealTask.query.filter_by(status='completed').count()
    in_progress = MealTask.query.filter_by(status='in_progress').count()
    planned = MealTask.query.filter_by(status='planned').count()

    # Calculate total cooking time
    tasks = MealTask.query.all()
    total_minutes = sum(task.duration_minutes for task in tasks if task.duration_minutes)

    return jsonify({
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'planned': planned,
        'total_cooking_time_minutes': total_minutes,
        'completion_percentage': round((completed / total_tasks * 100) if total_tasks > 0 else 0, 1)
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
