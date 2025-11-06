from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-is-a-test-website-just-be-chill' # Make sure this is a real secret!
socketio = SocketIO(app)

# This is the HTML, CSS, and JavaScript for the client's browser
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Chat</title>
    <style>
        body { font-family: sans-serif; }
        #chat-window {
            width: 500px; height: 300px;
            border: 1px solid #ccc;
            overflow-y: scroll;
            padding: 10px;
            margin-bottom: 10px;
        }
        #chat-messages { list-style: none; padding: 0; margin: 0; }
        #chat-messages li { padding: 5px 0; }
        #chat-form { display: flex; }
        #chat-input { flex-grow: 1; padding: 5px; }
    </style>
</head>
<body>
    <h1>Flask-SocketIO Chat</h1>
    <div id="chat-window">
        <ul id="chat-messages"></ul>
    </div>
    <form id="chat-form">
        <input id="chat-input" autocomplete="off" placeholder="Type a message..."/>
        <button>Send</button>
    </form>

    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    
    <script type="text/javascript">
        // 2. Connect to the server
        var socket = io();

        // 3. Get elements from the page
        var form = document.getElementById('chat-form');
        var input = document.getElementById('chat-input');
        var messages = document.getElementById('chat-messages');

        // 4. Client: Handle the form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Stop the page from reloading
            if (input.value) {
                // Send the message 'event' to the server
                socket.emit('send_message', { 'data': input.value });
                input.value = ''; // Clear the input box
            }
        });

        // 5. Client: Listen for 'receive_message' events from the server
        socket.on('receive_message', function(msg) {
            // Add the new message to the list
            var li = document.createElement('li');
            li.textContent = msg.data;
            messages.appendChild(li);
            // Scroll to the bottom
            var chatWindow = document.getElementById('chat-window');
            chatWindow.scrollTop = chatWindow.scrollHeight;
        });
    </script>
</body>
</html>
"""

# This route just serves the HTML page
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# 6. Server: Listen for 'send_message' events from any client
@socketio.on('send_message')
def handle_message(msg):
    # 'msg' is the dictionary {'data': 'Hello!'} sent by the client
    print('Message received: ' + msg['data'])
    
    # 7. Server: Emit a 'receive_message' event to ALL connected clients
    emit('receive_message', msg, broadcast=True)
