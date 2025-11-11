# Application Architecture Guide

## Overview

Your Thanksgiving Meal Planner is a full-stack web application built with:
- **Frontend**: HTML, CSS, JavaScript (Vanilla JS)
- **Backend**: Python Flask (REST API)
- **Database**: SQLite with SQLAlchemy ORM
- **Architecture**: Traditional Client-Server with REST API

```
┌─────────────────┐         HTTP/JSON          ┌─────────────────┐
│                 │  ←─────────────────────→   │                 │
│   Web Browser   │                            │  Flask Server   │
│  (JavaScript)   │   GET /api/tasks           │   (Python)      │
│                 │   PUT /api/tasks/1         │                 │
└─────────────────┘                            └────────┬────────┘
                                                        │
                                                        │ SQLAlchemy
                                                        │ ORM
                                                        ↓
                                                ┌─────────────────┐
                                                │                 │
                                                │  SQLite DB      │
                                                │  thanksgiving.db│
                                                │                 │
                                                └─────────────────┘
```

## Component Breakdown

### 1. Database Layer (`models.py`)

**What it does**: Defines the structure of your data and how it's stored in the database.

```python
class MealTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='planned')
    # ... other fields
```

**Key Concepts**:
- **ORM (Object-Relational Mapping)**: Instead of writing SQL, you work with Python objects
- **Table**: `MealTask` becomes a table named `meal_tasks` in the database
- **Columns**: Each field becomes a column in the table
- **Methods**: `to_dict()` converts database objects to JSON for the API

**Example Database Record**:
```
id | name          | status      | category | priority | ...
---+---------------+-------------+----------+----------+----
1  | Roast Turkey  | planned     | main     | 1        | ...
2  | Stuffing      | in_progress | side     | 2        | ...
```

### 2. Backend API (`app.py`)

**What it does**: The "brain" of your application that handles requests and talks to the database.

#### Application Setup

```python
app = Flask(__name__)  # Create Flask app
CORS(app)  # Allow browser to make requests from different origins

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thanksgiving.db'
db.init_app(app)  # Connect database to Flask
```

#### Data Initialization

When the app starts, it:
1. Creates the database tables if they don't exist (`db.create_all()`)
2. Checks if the database is empty
3. If empty, adds 10 sample Thanksgiving meal tasks

#### API Endpoints (Routes)

Think of routes as "functions that respond to web requests":

**GET /api/tasks** - List all tasks
```python
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = MealTask.query.order_by(MealTask.priority).all()
    return jsonify([task.to_dict() for task in tasks])
```
- Queries all tasks from database
- Orders them by priority
- Converts to JSON and returns

**PUT /api/tasks/<id>** - Update a task
```python
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = MealTask.query.get_or_404(task_id)
    data = request.json

    if 'status' in data:
        task.status = data['status']  # Update status

    db.session.commit()  # Save to database
    return jsonify(task.to_dict())
```
- Finds task by ID (or returns 404 if not found)
- Updates fields from request data
- Saves changes to database
- Returns updated task

**GET /api/stats** - Get statistics
```python
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_tasks = MealTask.query.count()
    completed = MealTask.query.filter_by(status='completed').count()
    # ... calculate other stats
    return jsonify({...})
```
- Queries database for counts
- Calculates percentages
- Returns summary statistics

### 3. Frontend (`static/index.html`)

**What it does**: The user interface that runs in the browser.

#### HTML Structure

```html
<div class="stats-grid">
    <!-- Statistics cards -->
</div>

<div class="controls">
    <!-- Filter buttons -->
</div>

<div class="tasks-grid" id="tasks-container">
    <!-- Task cards rendered by JavaScript -->
</div>
```

#### JavaScript Functions

**loadTasks()** - Fetch and display tasks
```javascript
async function loadTasks() {
    // 1. Make HTTP request to backend
    const response = await fetch('/api/tasks');

    // 2. Parse JSON response
    allTasks = await response.json();

    // 3. Update the UI
    renderTasks();
}
```

**renderTasks()** - Create HTML for each task
```javascript
function renderTasks() {
    const container = document.getElementById('tasks-container');

    // Filter tasks based on current filter
    let filteredTasks = allTasks.filter(...);

    // Create HTML for each task
    container.innerHTML = filteredTasks.map(task => `
        <div class="task-card">
            <div class="task-name">${task.name}</div>
            ...
        </div>
    `).join('');
}
```

**updateTaskStatus()** - Change task status
```javascript
async function updateTaskStatus(taskId, newStatus) {
    // 1. Send update request to backend
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });

    // 2. If successful, reload all tasks
    if (response.ok) {
        await loadTasks();
    }
}
```

## Request Flow Example

Let's trace what happens when you click "Start Cooking" on the Turkey task:

```
1. USER CLICKS BUTTON
   └─> onclick="updateTaskStatus(1, 'in_progress')"

2. JAVASCRIPT FUNCTION EXECUTES
   └─> async function updateTaskStatus(1, 'in_progress')
       └─> fetch('PUT /api/tasks/1', body: {status: 'in_progress'})

3. HTTP REQUEST SENT TO SERVER
   └─> PUT http://localhost:8000/api/tasks/1
       Headers: Content-Type: application/json
       Body: {"status": "in_progress"}

4. FLASK RECEIVES REQUEST
   └─> @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
       └─> def update_task(task_id=1):

5. DATABASE QUERY
   └─> task = MealTask.query.get_or_404(1)  # Find turkey task
       └─> SELECT * FROM meal_tasks WHERE id = 1

6. UPDATE DATABASE
   └─> task.status = 'in_progress'
       └─> db.session.commit()
           └─> UPDATE meal_tasks SET status='in_progress' WHERE id=1

7. RETURN RESPONSE
   └─> return jsonify(task.to_dict())
       └─> HTTP 200 OK
           Body: {"id": 1, "name": "Roast Turkey", "status": "in_progress", ...}

8. JAVASCRIPT RECEIVES RESPONSE
   └─> if (response.ok) { await loadTasks(); }

9. RELOAD ALL TASKS
   └─> fetch('GET /api/tasks')
       └─> Queries database for all tasks
           └─> Returns updated list

10. UPDATE UI
    └─> renderTasks()
        └─> Rebuilds HTML with new task states
            └─> Turkey card now shows "in_progress" badge
            └─> Button changes to "Mark Complete"
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User sees task cards                                   │
│     ↓                                                       │
│  2. Clicks "Start Cooking" button                          │
│     ↓                                                       │
│  3. updateTaskStatus(1, 'in_progress') called              │
│     ↓                                                       │
│  4. fetch() sends HTTP PUT request                         │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP PUT /api/tasks/1
                        │ {"status": "in_progress"}
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  5. Flask receives request at update_task() route          │
│     ↓                                                       │
│  6. Extracts task_id (1) and data                          │
│     ↓                                                       │
│  7. Query database: MealTask.query.get(1)                  │
│     ↓                                                       │
│  8. Update: task.status = 'in_progress'                    │
│     ↓                                                       │
│  9. Save: db.session.commit()                              │
│     ↓                                                       │
│  10. Return: jsonify(task.to_dict())                       │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP 200 OK
                        │ {"id": 1, "status": "in_progress", ...}
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  11. Response received successfully                         │
│     ↓                                                       │
│  12. Call loadTasks() to refresh data                      │
│     ↓                                                       │
│  13. fetch() GET /api/tasks                                │
│     ↓                                                       │
│  14. Receive all tasks (including updated turkey)          │
│     ↓                                                       │
│  15. renderTasks() rebuilds the HTML                       │
│     ↓                                                       │
│  16. User sees updated card with new status                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts Explained

### 1. REST API (REpresentational State Transfer)

A way for the frontend and backend to communicate using HTTP:

- **GET**: Read data ("Get me all tasks")
- **POST**: Create data ("Create a new task")
- **PUT**: Update data ("Update task #1")
- **DELETE**: Remove data ("Delete task #3")

### 2. JSON (JavaScript Object Notation)

A format for sending data between frontend and backend:

```javascript
// JavaScript object
{
  "id": 1,
  "name": "Roast Turkey",
  "status": "planned"
}
```

### 3. Asynchronous JavaScript (async/await)

Allows the browser to do other things while waiting for server responses:

```javascript
async function loadTasks() {
    // "await" pauses here until response arrives
    const response = await fetch('/api/tasks');

    // Then continues with the data
    const tasks = await response.json();
}
```

### 4. Single Page Application (SPA) Pattern

- Page loads once
- JavaScript updates content dynamically
- No full page refreshes needed
- Feels faster and more responsive

### 5. Database Sessions

```python
db.session.add(task)      # Stage changes
db.session.commit()       # Save to database
db.session.rollback()     # Undo if error
```

## File Structure Explained

```
app/
├── app.py              # Main application file
│   ├── Flask setup
│   ├── Database initialization
│   ├── Sample data creation
│   └── API routes (endpoints)
│
├── models.py           # Database models (table definitions)
│   └── MealTask class
│
├── requirements.txt    # Python dependencies
│   ├── Flask
│   ├── Flask-SQLAlchemy
│   └── Flask-CORS
│
├── static/             # Frontend files
│   └── index.html      # UI + JavaScript
│       ├── HTML structure
│       ├── CSS styles
│       └── JavaScript logic
│
└── thanksgiving.db     # SQLite database file (auto-created)
```

## Common Operations

### How filtering works

```javascript
// User clicks "Sides" button
function filterTasks('side') {
    currentFilter = 'side';

    // Filter the existing tasks array
    filteredTasks = allTasks.filter(task => task.category === 'side');

    // Re-render with only side dishes
    renderTasks();
}
```

### How stats are calculated

```python
# Count tasks by status
total_tasks = MealTask.query.count()
completed = MealTask.query.filter_by(status='completed').count()

# Calculate percentage
completion_percentage = (completed / total_tasks * 100) if total_tasks > 0 else 0
```

### How auto-refresh works

```javascript
// Reload tasks every 30 seconds
setInterval(() => {
    loadTasks();
}, 30000);  // 30000 milliseconds = 30 seconds
```

## Security & Best Practices

### CORS (Cross-Origin Resource Sharing)
```python
CORS(app)  # Allows browser to make requests
```

### Error Handling
```python
task = MealTask.query.get_or_404(task_id)  # Returns 404 if not found
```

### SQL Injection Prevention
SQLAlchemy automatically escapes inputs:
```python
# Safe - SQLAlchemy handles this properly
task = MealTask.query.filter_by(status=user_input).first()
```

## Next Steps to Learn More

1. **Modify a feature**: Try changing the colors or adding a new field
2. **Add an endpoint**: Create a `POST /api/tasks` to add new dishes
3. **Add validation**: Prevent empty task names
4. **Add sorting**: Sort by start time or duration
5. **Add search**: Filter tasks by name or ingredient

## Debugging Tips

### Check if server is running:
```bash
curl http://localhost:8000/health
```

### View database contents:
```bash
sqlite3 app/thanksgiving.db "SELECT * FROM meal_tasks;"
```

### Check browser console:
- Open browser DevTools (F12)
- Go to Console tab
- See JavaScript errors and logs

### Check network requests:
- Open browser DevTools (F12)
- Go to Network tab
- See all API calls and responses

## Summary

Your app is a **3-tier architecture**:

1. **Presentation Tier** (Frontend): HTML/CSS/JS in the browser
2. **Application Tier** (Backend): Flask API handling business logic
3. **Data Tier** (Database): SQLite storing persistent data

They communicate via **HTTP requests** using **JSON data**, following **REST** principles. The frontend makes requests, the backend processes them and talks to the database, then sends responses back to update the UI.

It's like a restaurant:
- **Frontend** = Menu and dining room (what customers see)
- **Backend** = Kitchen and waiters (processing orders)
- **Database** = Pantry and freezer (storing ingredients)
