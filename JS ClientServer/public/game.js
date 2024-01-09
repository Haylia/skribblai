var socket = null;

//Prepare game
var app = new Vue({
  el: "#game",
  data: {
    connected: false,
    canvas_setup: false,
    error: null,
    messages: [],
    chatmessage: "",
    me: { name: "", username: "", state: 0, score: 0 },
    state: { state: false },
    players: {},
    username: "",
    password: "",
    prompt: "",
    image: "",
  },
  mounted: function () {
    connect();
  },
  methods: {
    admin(command) {
      socket.emit("admin", command);
    },
    handleChat(message) {
      const messages = document.getElementById("messages");
      var item = document.createElement("li");
      item.textContent = message;
      messages.prepend(item);
    },
    fail(message) {
      this.error = message;
      setTimeout(clearError, 3000);
    },
    chat() {
      socket.emit("chat", this.chatmessage);
      this.chatmessage = "";
    },
    login() {
      socket.emit("login", {
        username: this.username,
        password: this.password,
      });
    },
    register() {
      socket.emit("register", {
        username: this.username,
        password: this.password,
      });
    },
    update(data) {
      this.me = data.me;
      this.state = data.state;
      this.players = data.players;
      if(!this.canvas_setup) {
        try{
          setup_canvas();
          this.canvas_setup = true;
        } catch (e) {
          console.log(e);
        }
      }
    },
  },
});

function setup_canvas() {
  const canvas = document.getElementById('drawing-board');
  const toolbar = document.getElementById('toolbar');
  const ctx = canvas.getContext('2d');

  const canvasOffsetX = canvas.offsetLeft;
  const canvasOffsetY = canvas.offsetTop;

  canvas.width = window.innerWidth / 2; // - (canvasOffsetX);
  canvas.height = window.innerHeight / 2; //- (canvasOffsetY);

  let isPainting = false;
  let lineWidth = 5;
  let startX;
  let startY;

  toolbar.addEventListener('click', e => {
      if (e.target.id === 'clear') {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
  });

  toolbar.addEventListener('change', e => {
      if(e.target.id === 'stroke') {
          ctx.strokeStyle = e.target.value;
      }

      if(e.target.id === 'lineWidth') {
          lineWidth = e.target.value;
      }
      
  });

  const draw = (e) => {
      if(!isPainting) {
          return;
      }

      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';

      ctx.lineTo(e.clientX - (canvasOffsetX/2.05), e.clientY - canvasOffsetY);
      ctx.stroke();

      app.image = canvas.toDataURL();
  }

  canvas.addEventListener('mousedown', (e) => {
      isPainting = true;
      startX = e.clientX;
      startY = e.clientY;
  });

  canvas.addEventListener('mouseup', e => {
      isPainting = false;
      ctx.stroke();
      ctx.beginPath();
  });

  canvas.addEventListener('mousemove', draw);
}

function clearError() {
  app.error = null;
}

function connect() {
  //Prepare web socket
  socket = io();

  //Connect
  socket.on("connect", function () {
    //Set connected state to true
    app.connected = true;
  });

  //Handle connection error
  socket.on("connect_error", function (message) {
    alert("Unable to connect: " + message);
  });

  //Handle disconnection
  socket.on("disconnect", function () {
    alert("Disconnected");
    app.connected = false;
  });

  //Handle error
  socket.on("fail", function (message) {
    app.fail(message);
  });

  //Handle incoming chat message
  socket.on("chat", function (message) {
    app.handleChat(message);
  });

  //Handle state
  socket.on("state", function (state) {
    app.update(state);
  });

  socket.on("register", ({ result, message }) => {
    if (!result) alert(message + " register failed");
    else app.state == 0;
  });
  socket.on("login", ({ result, message }) => {
    if (!result) {
      alert(message + " loging failed");
    } else app.state == 0;
  });
}
