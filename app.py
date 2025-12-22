from flask import Flask,render_template,request,redirect,url_for,session
import pymysql

#from jarvis import get_jarvis_response
from flask import jsonify, request

app=Flask(__name__)
app.secret_key="college_mini_project_key"
#functions to connect to your MySQl database

def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="soumya4096",
        database="quora_mini", 
        cursorclass=pymysql.cursors.DictCursor

    )
#the opening page (login) 
@app.route('/')
def index():
    return render_template('login.html')

# 2. THE LOGIN & PIN VERIFICATION LOGIC
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    pin = request.form['pin']
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if this User-ID (Name) already exists
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user:
        # If user exists, check if PIN matches
        if user['pin'] == pin:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return "<h1>Incorrect PIN! Go back and try again.</h1>"
    else:
        # If user doesn't exist, Create new account (Auto-Register)
        cursor.execute("INSERT INTO users (username, pin) VALUES (%s, %s)", (username, pin))
        db.commit()
        
        # Log them in immediately after creating account
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        new_user = cursor.fetchone()
        session['user_id'] = new_user['id']
        session['username'] = new_user['username']
        return redirect(url_for('dashboard'))




# Add these new routes to your app.py

@app.route('/post_question', methods=['POST'])
def post_question():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    content = request.form.get('content')
    user_id = session['user_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO questions (user_id, content) VALUES (%s, %s)", (user_id, content))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/upvote/<int:q_id>')
def upvote(q_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE questions SET upvotes = upvotes + 1 WHERE id = %s", (q_id,))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/reply/<int:q_id>', methods=['POST'])
def reply(q_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    reply_text = request.form.get('reply_text')
    user_id = session['user_id']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO answers (question_id, user_id, reply_text) VALUES (%s, %s, %s)", 
                   (q_id, user_id, reply_text))
    db.commit()
    return redirect(url_for('dashboard'))




@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get the word typed in the search bar
    search_query = request.args.get('search', '')
    
    db = get_db()
    cursor = db.cursor()
    
    if search_query:
        # Search filter: Looks for the word anywhere in the question content
        query = "SELECT questions.*, users.username FROM questions JOIN users ON questions.user_id = users.id WHERE questions.content LIKE %s ORDER BY created_at DESC"
        cursor.execute(query, ('%' + search_query + '%',))
    else:
        # No search: Show everything
        cursor.execute("SELECT questions.*, users.username FROM questions JOIN users ON questions.user_id = users.id ORDER BY created_at DESC")
    
    all_questions = cursor.fetchall()
    
    # Still fetch all answers so they show up under filtered questions
    cursor.execute("SELECT answers.*, users.username FROM answers JOIN users ON answers.user_id = users.id")
    all_answers = cursor.fetchall()
    
    return render_template('dashboard.html', 
                           user=session['username'], 
                           questions=all_questions, 
                           answers=all_answers,
                           search_query=search_query)



@app.route('/history')
def global_history():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    db = get_db()
    cursor = db.cursor()
    
    # This query gets the question text, the username, and the date
    cursor.execute("""
        SELECT questions.content, users.username, questions.created_at, questions.upvotes 
        FROM questions 
        JOIN users ON questions.user_id = users.id 
        ORDER BY questions.created_at DESC
    """)
    history_data = cursor.fetchall()
    
    return render_template('history.html', history=history_data)




@app.route('/jarvis_assist')
def jarvis_assist():
    # This gets the text you typed in the Jarvis box
    user_query = request.args.get('query')
    
    # This calls the Gemini function inside your jarvis.py
    ai_reply = get_jarvis_response(user_query)
    
    # This sends the answer back to your website screen
    return jsonify({"reply": ai_reply})



if __name__ == '__main__':
    app.run(debug=True)




