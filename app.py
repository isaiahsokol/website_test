from flask import (
    Flask, session, redirect, url_for, render_template_string, request
)
import time
import datetime
import random
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'a_very_random_and_secret_key_123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_results.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## MODIFIED: New Database Model for the 5-target game ##
class FiveTargetResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    average_difference = db.Column(db.Float, nullable=False)
    # Store all targets and actuals as strings for review
    all_targets = db.Column(db.String(200), nullable=False)
    all_actuals = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Game {self.id} (Avg Diff: {self.average_difference})>'

## MODIFIED: The HTML template for the 5-target game ##
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>5-Target Rhythm Game</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        .container { max-width: 600px; margin: auto; }
        .game-box { background: #f4f4f4; padding: 20px; border-radius: 8px; }
        .button {
            display: inline-block; font-size: 1.5em; padding: 20px 40px;
            cursor: pointer; border: none; border-radius: 5px;
            margin-top: 20px; width: 250px;
        }
        .start-game { background-color: #17a2b8; color: white; }
        .click-button { background-color: #007BFF; color: white; }
        
        .results-box { margin-top: 30px; }
        .results-box h2 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .results-list li { 
            background: #eee; margin: 5px; padding: 10px; 
            border-radius: 3px; text-align: left;
        }
        ul { list-style-type: none; padding-left: 0; }
        
        /* Styles for the game-in-progress */
        .target-list { list-style-type: decimal; padding-left: 30px; text-align: left; }
        .target-list li { 
            margin: 10px 0; font-size: 1.2em;
            background-color: white; padding: 8px; border-radius: 4px;
        }
        .target-list .completed { text-decoration: line-through; color: #888; }
        
        /* Style for the results table */
        table { width: 100%; margin-top: 20px; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 10px; }
        th { background-color: #f0f0f0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>5-Target Rhythm Game</h1>
        <div class="game-box">
            <form action="/" method="POST">
                
                {% if not game_in_progress %}
                    <p>Click to start! A single timer will begin, and you must
                       click 5 times to match the 5 targets.</p>
                    <button type="submit" name="action" value="start_game" 
                            class="button start-game">Start New Game</button>

                {% else %}
                    <h2>Click {{ click_count + 1 }} of 5</h2>
                    <p>Timer is running!</p>
                    <button type="submit" name="action" value="click" 
                            class="button click-button">Click!</button>

                    <h3>Targets:</h3>
                    <ul class="target-list">
                        {% for t in target_times %}
                            <li class="{{ 'completed' if loop.index0 < click_count }}">
                                <strong>Target: {{ '%.3f'|format(t) }}s</strong>
                                {% if loop.index0 < click_count %}
                                 (Your time: {{ '%.3f'|format(actual_times[loop.index0]) }}s)
                                {% endif %}
                            </li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </form>
        </div>

        {% if last_game_summary %}
        <div class="results-box">
            <h2>Last Game Results:</h2>
            
            <h3>Average Difference: 
                <strong>{{ '%.3f'|format(last_game_summary.average_diff) }}s</strong>
            </h3>
            
            <table>
                <tr>
                    <th>Target</th>
                    <th>Your Time</th>
                    <th>Difference</th>
                </tr>
                {% for i in range(5) %}
                <tr>
                    <td>{{ '%.3f'|format(last_game_summary.targets[i]) }}s</td>
                    <td>{{ '%.3f'|format(last_game_summary.actuals[i]) }}s</td>
                    <td>{{ '%.3f'|format(last_game_summary.diffs[i]) }}s</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}

        <div class="results-box">
            <h2>Leaderboard (Best Average Score)</h2>
            {% if all_results %}
                <ul class="results-list">
                {% for result in all_results %}
                    <li>
                        <strong>{{ '%.3f'|format(result.average_difference) }}s (avg)</strong>
                        <span style="font-size: 0.9em; color: #555;">
                            on {{ result.timestamp.strftime('%Y-%m-%d %H:%M') }}
                        </span>
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p>No results saved yet. Play a game!</p>
            {% endif %}
        </div>
        <a href="/reset" style="margin-top: 20px; display:block;">Clear Session</a>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    
    if request.method == 'POST':
        action = request.form.get('action')

        # --- State 1: User clicked "Start New Game" ---
        if action == 'start_game':
            # Generate 5 random times between 5 and 60 seconds
            targets = [random.uniform(5, 60) for _ in range(5)]
            # Sort them so they are in order
            targets.sort()
            
            session['target_times'] = targets
            session['start_time'] = time.time()
            session['game_in_progress'] = True
            session['click_count'] = 0
            session['actual_times'] = []
            session.pop('last_game_summary', None) # Clear old summary

        # --- State 2: User clicked "Click!" ---
        elif action == 'click' and session.get('game_in_progress'):
            # 1. Record the click
            start_time = session['start_time']
            elapsed = time.time() - start_time
            
            session['actual_times'].append(elapsed)
            session['click_count'] += 1
            session.modified = True # Tell Flask the session list was changed
            
            # 2. Check if game is over (5 clicks recorded)
            if session['click_count'] >= 5:
                # --- GAME IS OVER ---
                targets = session.pop('target_times')
                actuals = session.pop('actual_times')
                
                # Calculate differences
                differences = [abs(a - t) for a, t in zip(actuals, targets)]
                avg_diff = sum(differences) / len(differences)
                
                # Format for database strings
                targets_str = ", ".join([f"{t:.3f}" for t in targets])
                actuals_str = ", ".join([f"{a:.3f}" for a in actuals])
                
                # Save to database
                new_result = FiveTargetResult(
                    average_difference=avg_diff,
                    all_targets=targets_str,
                    all_actuals=actuals_str
                )
                db.session.add(new_result)
                db.session.commit()
                
                # Store summary in session to display it
                session['last_game_summary'] = {
                    'average_diff': avg_diff,
                    'targets': targets,
                    'actuals': actuals,
                    'diffs': differences
                }
                
                # Clear game-in-progress state
                session.pop('game_in_progress')
                session.pop('start_time')
                session.pop('click_count')
        
        # Always redirect after a POST
        return redirect(url_for('index'))

    # --- This is the GET logic (when the page loads) ---
    
    # Query database for all results, ordered by best score (lowest avg)
    all_results = FiveTargetResult.query.order_by(
        FiveTargetResult.average_difference.asc()
    ).all()

    return render_template_string(
        HTML_TEMPLATE,
        game_in_progress=session.get('game_in_progress', False),
        click_count=session.get('click_count', 0),
        target_times=session.get('target_times', []),
        actual_times=session.get('actual_times', []),
        last_game_summary=session.get('last_game_summary', None),
        all_results=all_results
    )

@app.route('/reset')
def reset():
    # Clear all game state from the session
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates the new FiveTargetResult table
    app.run(debug=False, host = '0.0.0.0')
