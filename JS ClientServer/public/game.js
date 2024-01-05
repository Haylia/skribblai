var socket = null;

//Prepare game
var app = new Vue({
  el: "#game",
  data: {
    connected: false,
    error: null,
    messages: [],
    chatmessage: "",
    me: { name: "", username: "", state: 0, score: 0 },
    state: { state: false },
    players: {},
    username: "",
    password: "",
    prompt: "",
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
    },
  },
});

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
