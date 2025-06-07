from flask import Flask, render_template, request, redirect,jsonify
from datetime import datetime, timedelta
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import numpy as np

app = Flask(__name__)

# Create the database and table if not exists
def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            task_description TEXT,
            project_name TEXT,
            priority INTEGER,
            task_deadline TEXT,
            pomodoros INTEGER,
            completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    
   
    conn = sqlite3.connect("records.db")
    cursor = conn.cursor()
   

    # Create table query
    create_table_query = """
    CREATE TABLE IF NOT EXISTS records(
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT ,
        project_name TEXT ,
        start_time TIME ,
        pause_time TIME
    );
    """


    # Execute the query
    cursor.execute(create_table_query)
    # Commit and close the connection
    conn.commit()
    conn.close()

init_db()




class Task:
    def __init__(self, id, name, description, project, priority, deadline, pomodoros,completed):
        self.id = id
        self.name = name
        self.description = description
        self.project = project
        self.priority = priority  # Urgency: 1 (low) to 4 (high)
        self.deadline = deadline  # Task deadline (YYYY-MM-DD)
        self.pomodoros = pomodoros
        self.completed=completed

    def __lt__(self, other):
        """
        Defines comparison for max-heap:
        - Higher priority tasks come first.
        - If priority is the same, today's tasks come first.
        - If both priority and date are the same, earlier added tasks come first.
        """
        if self.priority != other.priority:
            return self.priority < other.priority  # Max heap logic (higher value is higher priority)
        if self.deadline != other.deadline:
            return self.deadline < other.deadline  # Today's tasks should come first
        return self.id > other.id  # Lower ID means added earlier, so higher priority

class MaxHeap:
    def __init__(self):
        self.heap = []

    def push(self, task):
        """Insert a new task into the heap."""
        self.heap.append(task)
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """Removes and returns the highest-priority task (max-heap)."""
        if len(self.heap) == 0:
            return None  # Heap is empty

        if len(self.heap) == 1:
            return self.heap.pop()  # Only one element

        # Swap root (max element) with the last element
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]

        # Remove the last element (previous root)
        max_task = self.heap.pop()

        # Restore heap property
        self._heapify_down(0)

        return max_task

    def _heapify_up(self, index):
        """Moves a node up to restore the heap property."""
        parent = (index - 1) // 2
        while index > 0 and self.heap[parent] < self.heap[index]:
            self.heap[parent], self.heap[index] = self.heap[index], self.heap[parent]
            index = parent
            parent = (index - 1) // 2

    def _heapify_down(self, index):
        """Moves a node down to restore the max-heap property."""
        size = len(self.heap)

        while True:
            largest = index  # Assume parent is the largest
            left = 2 * index + 1
            right = 2 * index + 2

            # Check if left child is greater
            if left < size and self.heap[left] > self.heap[largest]:
                largest = left

            # Check if right child is greater
            if right < size and self.heap[right] > self.heap[largest]:
                largest = right

            # If the largest is not the parent, swap and continue
            if largest != index:
                self.heap[index], self.heap[largest] = self.heap[largest], self.heap[index]
                index = largest  # Move down
            else:
                break  # Heap property is restored

    def get_all_tasks(self):
        """Returns all tasks in sorted order (highest priority first)."""
        sorted_tasks = []
        while self.heap:
            sorted_tasks.append(self.pop())
        return sorted_tasks



def get_filtered_tasks():
    """Fetches tasks with deadlines today or tomorrow from SQLite and sorts them using a max-heap."""
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    today = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Fetch tasks with deadline today or tomorrow
    cursor.execute("""
        SELECT id, task_name, task_description, project_name, priority, task_deadline, pomodoros,completed
        FROM tasks 
        WHERE (task_deadline = ? OR task_deadline = ?) AND completed=0;
    """, (today, tomorrow))

    rows = cursor.fetchall()
    conn.close()

    # Create a max-heap
    task_heap = MaxHeap()

    # Insert tasks into heap
    for row in rows:
        task = Task(*row)  # Unpack row into Task object
        task_heap.push(task)

    # Retrieve sorted tasks
    return task_heap.get_all_tasks()


   







@app.route("/", methods=["GET", "POST"])
def intropage():
    return render_template("introdemo.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/main", methods=["GET","POST"])
def main():

   
    

    """Renders the HTML page with sorted task recommendations."""
    tasks = get_filtered_tasks()
    tasks = tasks[::-1]


    return render_template("main3.html", tasks=tasks )
        
@app.route("/main/records", methods=["POST"])
def main1():

   
    data = request.get_json()  # Get data from JavaScript
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    
    task_id = data.get("task_id1")
    completed = data.get("completed1") 
    
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    if(completed==1):
        cursor.execute("UPDATE tasks SET completed=? WHERE id=?",(1,task_id)) 
    conn.commit()
    conn.close()

    return jsonify({"message": "Hello from main1!"})


@app.route("/calender", methods=["GET", "POST"])
def calender():
    if request.method == "POST":
        task_name = request.form["task_name"]
        task_description = request.form["task_description"]
        project_name = request.form["project_name"]
        priority = request.form["priority"]
        task_deadline = request.form["task_deadline"]
        task_deadline = datetime.strptime(task_deadline, "%Y-%m-%d").date()
        pomodoros = request.form["pomodoros"]

        # Insert data into database
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task_name, task_description, project_name, priority, task_deadline, pomodoros) VALUES (?, ?, ?, ?, ?, ?)",
                       (task_name, task_description, project_name, priority, task_deadline, pomodoros))
        conn.commit()
        conn.close()
        

    return render_template("demo19.html")


@app.route("/completed", methods=["GET", "POST"])
def completed():


    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE completed=1 ;")
    tasks = cursor.fetchall()
    conn.commit()
    conn.close()

    return render_template("completed.html", tasks=tasks )




@app.route("/remaining", methods=["GET", "POST"])
def remaining():


    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    if request.method == "POST":

        form_name = request.form.get("form_name")  # Identify the form

        if form_name == "task_form":

            task_id= int(request.form["task_id"])
            task_name = request.form["task_name"]
            task_description = request.form["task_description"]
            project_name = request.form["project_name"]
            priority = request.form["priority"]
            task_deadline = request.form["task_deadline"]
            task_deadline = datetime.strptime(task_deadline, "%Y-%m-%d").date()
            pomodoros = request.form["pomodoros"]

            if task_id == 0:
                
                cursor = conn.cursor()
                
                cursor.execute("INSERT INTO tasks(task_name, task_description, project_name, priority, task_deadline, pomodoros) VALUES (?, ?, ?, ?, ?, ?)",
                            (task_name, task_description, project_name, priority, task_deadline, pomodoros))
                conn.commit()

            else:
                cursor = conn.cursor()
                cursor.execute("""UPDATE tasks SET task_name = ?, task_description = ? , project_name = ? , priority = ? , task_deadline = ? ,
                                pomodoros = ? WHERE id = ?""",
                        (task_name, task_description, project_name, priority, task_deadline, pomodoros,task_id))
                conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE DATE(task_deadline) < DATE('now') AND completed=0 ;")
    tasks = cursor.fetchall()
    conn.commit()
    conn.close()

    return render_template("remaining.html", tasks=tasks )







@app.route("/today", methods=["GET", "POST"])
def today():
    conn = sqlite3.connect("tasks.db")
    current_date = datetime.today()
    if request.method == "POST":

        form_name = request.form.get("form_name")  # Identify the form

        if form_name == "task_form":

            task_id= int(request.form["task_id"])
            task_name = request.form["task_name"]
            task_description = request.form["task_description"]
            project_name = request.form["project_name"]
            priority = request.form["priority"]
            task_deadline = request.form["task_deadline"]
            task_deadline = datetime.strptime(task_deadline, "%Y-%m-%d").date()
            pomodoros = request.form["pomodoros"]

            if task_id == 0:
                
                cursor = conn.cursor()
                
                cursor.execute("INSERT INTO tasks(task_name, task_description, project_name, priority, task_deadline, pomodoros) VALUES (?, ?, ?, ?, ?, ?)",
                            (task_name, task_description, project_name, priority, task_deadline, pomodoros))
                conn.commit()

            else:
                cursor = conn.cursor()
                cursor.execute("""UPDATE tasks SET task_name = ?, task_description = ? , project_name = ? , priority = ? , task_deadline = ? ,
                                pomodoros = ? WHERE id = ?""",
                        (task_name, task_description, project_name, priority, task_deadline, pomodoros,task_id))
                conn.commit()

        elif form_name == "revive_form":
            revive_date = request.form["revive-date"]
            cursor = conn.cursor()
                
            cursor.execute("""UPDATE tasks SET task_deadline = ? 
                           WHERE task_deadline = ?""",(revive_date , (current_date-timedelta(days=1)).strftime("%Y-%m-%d")))
            conn.commit()
    conn.close()


    
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_deadline = ? AND completed=0 ;",(current_date.strftime("%Y-%m-%d"),))
    tasks_today = cursor.fetchall()

    
    cursor.execute("SELECT * FROM tasks WHERE task_deadline = ? AND completed=0 ;",((current_date-timedelta(days=1)).strftime("%Y-%m-%d"),))
    tasks_yesterday = cursor.fetchall()

    conn.close()

    # Number of days to add (change as needed)
    days_to_add = 7

    days_to_revive=[]  

    # Loop to add days one by one
    for i in range(days_to_add):
        new_date = current_date + timedelta(days=i)
        days_to_revive.append(new_date.strftime("%Y-%m-%d"))
        print(new_date.strftime("%Y-%m-%d"))
        
      

    return render_template("demo17.html", tasks_today=tasks_today , days_to_revive=days_to_revive ,tasks_yesterday=tasks_yesterday)
        

@app.route("/tasks")
def tasks():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return render_template("result.html", tasks=tasks)


def plot_to_base64():
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Function to calculate time difference in minutes
def calculate_time_difference(start_time, pause_time):
    try:
        fmt = "%H:%M:%S"  # Define time format (HH:MM:SS)
        t1 = datetime.strptime(start_time, fmt)
        t2 = datetime.strptime(pause_time, fmt)
        return (t2 - t1).seconds / 60  # Convert seconds to minutes
    except:
        return 0  # Return 0 if data is invalid

@app.route('/plots')
def plots():
    # Connect to the SQLite database
    conn = sqlite3.connect("records.db")
    cursor = conn.cursor()

    # --- Fetch Time Spent on Each Project ---
    cursor.execute("SELECT project_name, start_time, pause_time FROM records")
    records = cursor.fetchall()

    # Compute time spent for each project
    project_times = {}
    for project, start, pause in records:
        if project and start and pause:
            time_spent = calculate_time_difference(start, pause)
            project_times[project] = project_times.get(project, 0) + time_spent

    conn.close()

    # Convert data into DataFrame
    df = pd.DataFrame(list(project_times.items()), columns=["Project", "Time Spent"])

    # --- Bar Chart: Time Spent on Projects ---
    plt.figure(figsize=(8, 4))
    plt.bar(df["Project"], df["Time Spent"], color='skyblue')
    plt.xlabel("Project")
    plt.ylabel("Time Spent (Minutes)")
    plt.title("Time Spent on Each Project")
    plt.xticks(rotation=45)
    time_spent_chart = plot_to_base64()
    plt.close()

    # --- Pie Chart: Completed vs. Incomplete Tasks ---
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT completed, COUNT(*) FROM tasks GROUP BY completed")
    task_data = cursor.fetchall()
    conn.close()

    # Extract data
    labels = ["Incomplete", "Completed"]
    sizes = [0, 0]  # Default values for incomplete(0) and completed(1)

    for completed, count in task_data:
        if completed == 0:
            sizes[0] = count
        elif completed == 1:
            sizes[1] = count

    # Generate pie chart
    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=["red", "green"], startangle=140)
    plt.title("Task Completion Status")
    task_completion_chart = plot_to_base64()
    plt.close()

    return render_template("plots.html", time_chart=time_spent_chart, task_chart=task_completion_chart)


if __name__ == "__main__":
    app.run(debug=True)
