import streamlit as st
from datetime import date
import backend_fit as db

# A simple user management system for a single user, using session state
# In a real app, this would be a more robust login system.
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

st.set_page_config(layout="wide")
st.title("💪 Personal Fitness Tracker")

# Login/Profile Management
if st.session_state.user_id is None:
    st.header("Login / Create Profile")
    st.info("Since this is a single-user app, we'll create or find your profile by email.")
    
    email = st.text_input("Enter your email:")
    
    if st.button("Find/Create Profile"):
        conn = db.get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM users WHERE email = %s;", (email,))
            user_data = cur.fetchone()
            conn.close()

            if user_data:
                st.session_state.user_id = user_data[0]
                st.session_state.user_name = user_data[1]
                st.success(f"Welcome back, {st.session_state.user_name}!")
                st.experimental_rerun()
            else:
                st.warning("Email not found. Let's create a new profile.")
                name = st.text_input("Your Full Name:")
                weight = st.number_input("Your Weight (kg):", min_value=1.0)
                if st.button("Create New Profile"):
                    new_user_id = db.create_user(name, email, weight)
                    if new_user_id:
                        st.session_state.user_id = new_user_id
                        st.session_state.user_name = name
                        st.success("Profile created successfully! Please log in again.")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create profile. Please try again.")
else:
    # Main Application
    st.sidebar.title(f"Welcome, {st.session_state.user_name}!")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear() or st.experimental_rerun())

    menu = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Log Workout", "Friends & Leaderboard", "Goals", "Business Insights"]
    )

    # --- Dashboard Section ---
    if menu == "Dashboard":
        st.header("Your Fitness Dashboard")
        st.write("Overview of your fitness journey.")
        
        # Display goals
        st.subheader("Your Goals")
        goals = db.read_goals(st.session_state.user_id)
        if goals:
            for goal in goals:
                goal_id, description, target, current = goal
                progress = (current / target) if target > 0 else 0
                st.write(f"**Goal:** {description}")
                st.progress(progress)
                st.write(f"Progress: {current} / {target}")
        else:
            st.info("You haven't set any goals yet. Go to the 'Goals' section to add one!")
        
        # Display recent workouts
        st.subheader("Recent Workouts")
        workouts = db.read_workouts(st.session_state.user_id)
        if workouts:
            for i, workout in enumerate(workouts[:3]): # Show last 3
                st.markdown(f"**Workout on {workout['date'].strftime('%Y-%m-%d')}** - Duration: {workout['duration']} min")
                for exercise in workout['exercises']:
                    st.write(f"- {exercise['name']}: {exercise['sets']} sets, {exercise['reps']} reps, {exercise['weight']} kg")
        else:
            st.info("No workouts logged yet. Start by logging one!")

    # --- Log Workout Section (Create) ---
    elif menu == "Log Workout":
        st.header("Log a New Workout")

        with st.form("new_workout_form"):
            workout_date = st.date_input("Date", date.today())
            duration = st.number_input("Duration (minutes)", min_value=1, value=30)
            
            st.subheader("Add Exercises")
            
            # Use a list to store exercise details
            if 'exercises' not in st.session_state:
                st.session_state.exercises = []

            exercise_name = st.text_input("Exercise Name:")
            sets = st.number_input("Sets:", min_value=1, value=3)
            reps = st.number_input("Reps:", min_value=1, value=10)
            weight = st.number_input("Weight (kg):", min_value=0.0, value=0.0)

            add_exercise = st.form_submit_button("Add Exercise to Workout")
            if add_exercise and exercise_name:
                st.session_state.exercises.append({
                    'name': exercise_name,
                    'sets': sets,
                    'reps': reps,
                    'weight': weight
                })
                st.success(f"Added {exercise_name} to workout.")

            st.write("---")
            st.subheader("Current Exercises for this Workout:")
            if st.session_state.exercises:
                for ex in st.session_state.exercises:
                    st.write(f"- **{ex['name']}**: {ex['sets']} sets, {ex['reps']} reps, {ex['weight']} kg")
            else:
                st.info("No exercises added yet.")

            submitted = st.form_submit_button("Log Workout")
            if submitted and st.session_state.exercises:
                success = db.create_workout(st.session_state.user_id, workout_date, duration, st.session_state.exercises)
                if success:
                    st.success("Workout logged successfully!")
                    st.session_state.exercises = [] # Clear exercises for new workout
                else:
                    st.error("Failed to log workout.")

    # --- Friends & Leaderboard Section (Create, Read, Delete) ---
    elif menu == "Friends & Leaderboard":
        st.header("Friends & Leaderboard")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Add a Friend")
            friend_email = st.text_input("Enter friend's email:")
            if st.button("Add Friend"):
                if db.create_friendship(st.session_state.user_id, friend_email):
                    st.success(f"Friend added!")
                else:
                    st.error("Failed to add friend. Check the email or if they are already your friend.")

        with col2:
            st.subheader("Remove a Friend")
            friends_list = db.read_friends(st.session_state.user_id)
            if friends_list:
                friend_emails = [f[1] for f in friends_list]
                friend_to_remove = st.selectbox("Select friend to remove:", friend_emails)
                if st.button("Remove Friend"):
                    if db.delete_friendship(st.session_state.user_id, friend_to_remove):
                        st.success(f"Removed {friend_to_remove}.")
                    else:
                        st.error("Failed to remove friend.")
            else:
                st.info("You have no friends yet.")

        st.subheader("Leadership Board")
        
        leaderboard_data = db.get_leaderboard(st.session_state.user_id)
        if leaderboard_data:
            st.write("Ranking based on total workout minutes this week:")
            # In a real app, you would filter by week. This is a simplified version.
            st.table(leaderboard_data)
        else:
            st.info("No leaderboard data available. Log a workout or add friends!")

    # --- Goals Section (Create, Read, Update, Delete) ---
    elif menu == "Goals":
        st.header("Set Your Goals")
        
        with st.form("goal_form"):
            st.subheader("Add a New Goal")
            goal_description = st.text_area("Goal Description (e.g., 'Workout 5 times a week')")
            target_value = st.number_input("Target Value (e.g., 5)", min_value=1)
            
            add_goal_button = st.form_submit_button("Add Goal")
            if add_goal_button and goal_description:
                if db.create_goal(st.session_state.user_id, goal_description, target_value):
                    st.success("Goal added successfully!")
                else:
                    st.error("Failed to add goal.")
        
        st.subheader("Your Current Goals")
        goals = db.read_goals(st.session_state.user_id)
        if goals:
            for goal in goals:
                goal_id, description, target, current = goal
                with st.expander(f"**{description}**"):
                    st.write(f"Target: {target}")
                    st.write(f"Current: {current}")
                    
                    new_current = st.number_input("Update Current Value:", min_value=0, value=current, key=f"update_val_{goal_id}")
                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.button("Update Progress", key=f"update_btn_{goal_id}"):
                            if db.update_goal(goal_id, description, target, new_current):
                                st.success("Goal updated!")
                            else:
                                st.error("Failed to update goal.")
                    with col_delete:
                        if st.button("Delete Goal", key=f"delete_btn_{goal_id}"):
                            if db.delete_goal(goal_id):
                                st.success("Goal deleted.")
                            else:
                                st.error("Failed to delete goal.")
        else:
            st.info("You have no goals set yet.")
            
    # --- Business Insights Section (Read) ---
    elif menu == "Business Insights":
        st.header("Your Fitness Insights")
        st.write("A summary of your fitness data.")
        
        insights = db.get_business_insights(st.session_state.user_id)
        
        if insights:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Workouts", value=insights.get('total_workouts', 0))
                st.metric(label="Total Duration (min)", value=insights.get('total_duration', 0))
            with col2:
                st.metric(label="Avg Duration (min)", value=f"{insights.get('avg_duration', 0):.2f}")
                st.metric(label="Min Workout Duration (min)", value=insights.get('min_duration', 0))
            with col3:
                st.metric(label="Max Weight Lifted (kg)", value=insights.get('max_weight_lifted', 0))
        else:
            st.info("No data available to generate insights. Log a workout first!")