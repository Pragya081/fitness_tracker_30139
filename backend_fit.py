import psycopg2

# Database configuration
DATABASE_CONFIG = {
    'dbname': 'Tracker',
    'user': 'postgres',
    'password': 'Pragya@123',
    'host': 'localhost',
    'port': '5432'
}

def get_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

# --- CRUD Operations for User Profile ---

def create_user(name, email, weight):
    """Creates a new user profile."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, weight_kg) VALUES (%s, %s, %s) RETURNING id;",
            (name, email, weight)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        print("Error: A user with this email already exists.")
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None
    finally:
        if conn: conn.close()

def read_user(user_id):
    """Retrieves a user's profile."""
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, weight_kg FROM users WHERE id = %s;",
            (user_id,)
        )
        user_data = cur.fetchone()
        return user_data
    except Exception as e:
        print(f"Error reading user data: {e}")
        return None
    finally:
        if conn: conn.close()

def update_user(user_id, name, email, weight):
    """Updates a user's profile."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET name = %s, email = %s, weight_kg = %s WHERE id = %s;",
            (name, email, weight, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False
    finally:
        if conn: conn.close()

def delete_user(user_id):
    """Deletes a user's profile."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if conn: conn.close()

# --- CRUD Operations for Workouts and Exercises ---

def create_workout(user_id, date, duration, exercises):
    """Creates a new workout and its associated exercises."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO workouts (user_id, workout_date, duration_minutes) VALUES (%s, %s, %s) RETURNING id;",
            (user_id, date, duration)
        )
        workout_id = cur.fetchone()[0]
        for exercise in exercises:
            cur.execute(
                "INSERT INTO exercises (workout_id, exercise_name, sets, reps, weight_kg) VALUES (%s, %s, %s, %s, %s);",
                (workout_id, exercise['name'], exercise['sets'], exercise['reps'], exercise['weight'])
            )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating workout: {e}")
        return False
    finally:
        if conn: conn.close()

def read_workouts(user_id):
    """Retrieves all workouts and exercises for a given user."""
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                w.id, w.workout_date, w.duration_minutes,
                e.exercise_name, e.sets, e.reps, e.weight_kg
            FROM workouts w
            JOIN exercises e ON w.id = e.workout_id
            WHERE w.user_id = %s
            ORDER BY w.workout_date DESC;
            """,
            (user_id,)
        )
        workout_data = cur.fetchall()
        
        workouts = {}
        for row in workout_data:
            workout_id, date, duration, name, sets, reps, weight = row
            if workout_id not in workouts:
                workouts[workout_id] = {
                    'date': date,
                    'duration': duration,
                    'exercises': []
                }
            workouts[workout_id]['exercises'].append({
                'name': name,
                'sets': sets,
                'reps': reps,
                'weight': weight
            })
        return list(workouts.values())
    except Exception as e:
        print(f"Error reading workouts: {e}")
        return []
    finally:
        if conn: conn.close()

# --- CRUD Operations for Friends ---

def create_friendship(user_id, friend_email):
    """Adds a friend to a user's friend list."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s;", (friend_email,))
        friend_id_data = cur.fetchone()
        if not friend_id_data:
            print("Friend not found.")
            return False
        friend_id = friend_id_data[0]

        cur.execute(
            "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s);",
            (user_id, friend_id)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        print("Friendship already exists.")
        return False
    except Exception as e:
        print(f"Error adding friend: {e}")
        return False
    finally:
        if conn: conn.close()

def read_friends(user_id):
    """Retrieves a list of a user's friends."""
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT u.name, u.email FROM friends f JOIN users u ON f.friend_id = u.id WHERE f.user_id = %s;",
            (user_id,)
        )
        friends = cur.fetchall()
        return friends
    except Exception as e:
        print(f"Error reading friends: {e}")
        return []
    finally:
        if conn: conn.close()

def delete_friendship(user_id, friend_email):
    """Removes a friend from a user's friend list."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s;", (friend_email,))
        friend_id_data = cur.fetchone()
        if not friend_id_data:
            print("Friend not found.")
            return False
        friend_id = friend_id_data[0]

        cur.execute(
            "DELETE FROM friends WHERE user_id = %s AND friend_id = %s;",
            (user_id, friend_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting friend: {e}")
        return False
    finally:
        if conn: conn.close()

# --- CRUD Operations for Goals ---

def create_goal(user_id, description, target_value):
    """Creates a new fitness goal."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO goals (user_id, description, target_value) VALUES (%s, %s, %s);",
            (user_id, description, target_value)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating goal: {e}")
        return False
    finally:
        if conn: conn.close()

def read_goals(user_id):
    """Retrieves a user's goals."""
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, description, target_value, current_value FROM goals WHERE user_id = %s;",
            (user_id,)
        )
        goals = cur.fetchall()
        return goals
    except Exception as e:
        print(f"Error reading goals: {e}")
        return []
    finally:
        if conn: conn.close()

def update_goal(goal_id, description, target_value, current_value):
    """Updates a fitness goal."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE goals SET description = %s, target_value = %s, current_value = %s WHERE id = %s;",
            (description, target_value, current_value, goal_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating goal: {e}")
        return False
    finally:
        if conn: conn.close()

def delete_goal(goal_id):
    """Deletes a fitness goal."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM goals WHERE id = %s;", (goal_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting goal: {e}")
        return False
    finally:
        if conn: conn.close()

# --- Business Insights and Leaderboard ---

def get_business_insights(user_id):
    """
    Provides various business insights using aggregate functions.
    The insights are for the current user.
    """
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        insights = {}
        
        # Total workouts COUNT
        cur.execute("SELECT COUNT(*) FROM workouts WHERE user_id = %s;", (user_id,))
        insights['total_workouts'] = cur.fetchone()[0]
        
        # Total workout duration SUM
        cur.execute("SELECT SUM(duration_minutes) FROM workouts WHERE user_id = %s;", (user_id,))
        insights['total_duration'] = cur.fetchone()[0] or 0
        
        # Average workout duration AVG
        cur.execute("SELECT AVG(duration_minutes) FROM workouts WHERE user_id = %s;", (user_id,))
        insights['avg_duration'] = cur.fetchone()[0] or 0
        
        # Max weight lifted (across all exercises) MAX
        cur.execute("""
            SELECT MAX(e.weight_kg) FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.user_id = %s;
        """, (user_id,))
        insights['max_weight_lifted'] = cur.fetchone()[0] or 0
        
        # Min duration MIN
        cur.execute("SELECT MIN(duration_minutes) FROM workouts WHERE user_id = %s;", (user_id,))
        insights['min_duration'] = cur.fetchone()[0] or 0
        
        return insights
    except Exception as e:
        print(f"Error getting business insights: {e}")
        return None
    finally:
        if conn: conn.close()

def get_leaderboard(user_id, metric='total_workout_minutes'):
    """
    Generates a leaderboard based on a selected metric.
    Ranks the user and their friends.
    """
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        
        # Get the user's friends' IDs and the user's own ID
        cur.execute(
            "SELECT friend_id FROM friends WHERE user_id = %s;",
            (user_id,)
        )
        friend_ids = [row[0] for row in cur.fetchall()]
        all_ids = friend_ids + [user_id]
        
        if not all_ids:
            return []

        # Get total workout minutes for each user (including the current user and friends)
        placeholders = ','.join(['%s'] * len(all_ids))
        query = f"""
            SELECT u.name, SUM(w.duration_minutes) AS total_minutes
            FROM users u
            JOIN workouts w ON u.id = w.user_id
            WHERE u.id IN ({placeholders})
            GROUP BY u.name
            ORDER BY total_minutes DESC;
        """
        cur.execute(query, tuple(all_ids))
        
        leaderboard = cur.fetchall()
        return leaderboard
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []
    finally:
        if conn: conn.close()