"use strict";

//Set up express
const express = require("express");
const app = express();

// const { createApp } = require('vue');
// const App = require('./public/App.vue');

// createApp(App).mount('#canvas');

//Setup socket.io
const server = require("http").Server(app);
const io = require("socket.io")(server);

let players = new Map();
let playersToSockets = new Map();
let socketsToPlayers = new Map();
let nextPlayerNumber = 0;
let state = { state: 0, countdown: 90 };
let timer = null;

//Setup static page handling
app.set("view engine", "ejs");
app.use("/static", express.static("public"));

//Handle client interface on /
app.get("/", (req, res) => {
  res.render("client");
});
//Handle display interface on /display
app.get("/display", (req, res) => {
  res.render("display");
});

// URL of the backend API
const BACKEND_ENDPOINT = process.env.BACKEND || "http://localhost:8181";
const axios = require("axios").create({ baseURL: BACKEND_ENDPOINT });

//Start the server
function startServer() {
  const PORT = process.env.PORT || 8080;
  server.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

//Handle errors
function error(socket, message, halt) {
  console.log("Error: " + message);
  socket.emit("fail", message);
  if (halt) {
    socket.disconnect();
  }
}

//Handle announcements
function announce(message) {
  console.log("Announcement: " + message);
  io.emit("chat", message);
}

//Handle join
function handleJoin(socket, username) {
  //Can only join the game before it has started
  if (state.state > 0) {
    error(socket, "The game has already started", true);
    return;
  }

  //Start new player
  nextPlayerNumber++;
  console.log("Welcome to player " + nextPlayerNumber);

  players.set(nextPlayerNumber, {
    name: nextPlayerNumber,
    username: username,
    state: 1,
    score: 0,
  });
  playersToSockets.set(nextPlayerNumber, socket);
  socketsToPlayers.set(socket, nextPlayerNumber);
}

//Handle login ( this login function should work but when i try with the excutable form CW login doesnt work but Register work
//                so  will try again with our deployment URL if done)
// function handleLogin(credentials, socket) {
//   let username = credentials.username;
//   let password = credentials.password;

//   const userInfo = { username, password };

//   sendLogin("/player/login", userInfo)
//     .then((response) => {
//       const { result, msg } = response.data;
//       if (result) {
//         handleJoin(socket, username);
//         updateAll();
//         socket.emit("login", { result, message: msg });
//       } else {
//         socket.emit("login", { result, message: msg });
//       }
//     })
//     .catch((error) => {
//       console.error(error);
//       socket.emit("login", false, "Error during login");
//     });
// }
// function sendLogin(url, userInfo) {
//   return axios.get(url, userInfo);
// }
function handleLogin(credentials, socket) {
  let username = credentials.username;
  let password = credentials.password;

  handleJoin(socket, username);
  updateAll();

  // Prepare user information for login
  // const userInfo = { username, password };
  // const config = createRequestConfig("login", "/player/login", userInfo);

  // sendLogin(config)
  //   .then((response) => {
  //     const { result, msg } = response.data;
  //     if (result) {
  //       // If login is successful
  //       handleJoin(socket, username);
  //       updateAll();
  //       socket.emit("login", { result, message: msg });
  //     } else {
  //       socket.emit("login", { result, message: msg });
  //     }
  //   })
  //   .catch((error) => {
  //     console.error(error);
  //     socket.emit("login", false, "Error during login");
  //   });
}

function sendLogin(config) {
  return axios.request(config);
}

function createRequestConfig(act, url, userInfo) {
  return {
    method: determineMethod(act),
    url: `http://localhost:8181${url}`, // CHANGE it url to deployment url
    headers: { "Content-Type": "text/plain" },
    data: userInfo,
  };
}

function determineMethod(act) {
  return act === "login" ? "get" : "post";
}
//Handle registration
function handleRegister(credentials, socket) {
  let username = credentials.username;
  let password = credentials.password;

  handleJoin(socket, username);
  updateAll();

  // const userInfo = { username, password };

  // sendRegister("/player/register", userInfo)
  //   .then((response) => {
  //     const { result, msg } = response.data;
  //     if (result) {
  //       // If registration is successful
  //       handleJoin(socket, username);
  //       updateAll();
  //       socket.emit("register", { result, message: msg });
  //     } else {
  //       socket.emit("register", { result, message: msg });
  //     }
  //   })
  //   .catch((error) => {
  //     console.error(error);
  //     socket.emit("register", false, "Error during registration");
  //   });
}

function sendRegister(url, userInfo) {
  return axios.post(url, userInfo);
}

//Update state of all players
function updateAll() {
  console.log("Updating all players");
  for (let [playerNumber, socket] of playersToSockets) {
    updatePlayer(socket);
  }
}

//Update one player
function updatePlayer(socket) {
  const playerNumber = socketsToPlayers.get(socket);
  const thePlayer = players.get(playerNumber);
  const data = {
    state: state,
    me: thePlayer,
    players: Object.fromEntries(players),
  };
  socket.emit("state", data);
}

//Handle admin actions
function handleAdmin(player, action) {
  if (player != 1) {
    console.log("Failed admin action from player " + player + " for " + action);
    return;
  }

  if (action == "start" && state.state == 0) {
    startGame();
  } else {
    console.log("Unknown admin action: " + action);
  }
}

//Start the game
function startGame() {
  console.log("Game starting");
  announce("Let the games begin");

  //Prepare all players
  for (const [playerNumber, player] of players) {
    player.state = 1;
  }

  //Start the timer
  console.log("Starting the timer: " + state.countdown);
  timer = setInterval(() => {
    tickGame();
  }, 1000);

  //Advance the game
  state.state = 1;
}

//Game tick
function tickGame() {
  if (state.countdown > 1) {
    state.countdown--;
    console.log("Tick " + state.countdown);
  } else {
    clearInterval(timer);
    timer = null;
    endGame();
  }
  updateAll();
}

//End game -> 2
function endGame() {
  state.state = 2;
  console.log("Game ending");
  for (let [playerNumber, player] of players) {
    if (player.score < 100) {
      console.log("Time up for " + player.username);
    }
  }
}

//Chat message
function handleChat(player, message) {
  console.log("Handling chat: " + message + " from player " + player);
  announce(player + ": " + message);
}

//Handle new connection
io.on("connection", (socket) => {
  console.log("New connection");

  //Handle on chat message received
  socket.on("chat", (message) => {
    if (!socketsToPlayers.has(socket)) return;
    let player = socketsToPlayers.get(socket);
    let thePlayer = players.get(player);
    handleChat(thePlayer.username, message);
  });

  //Handle admin command
  socket.on("admin", (action) => {
    if (!socketsToPlayers.has(socket)) return;
    handleAdmin(socketsToPlayers.get(socket), action);
    updateAll();
  });

  //Handle disconnection
  socket.on("disconnect", () => {
    console.log("Dropped connection");
  });

  //Handle login
  socket.on("login", (credentials) => {
    handleLogin(credentials, socket);
  });

  //Handle registration
  socket.on("register", (credentials) => {
    handleRegister(credentials, socket);
  });
});

//Start server
if (module === require.main) {
  startServer();
}

module.exports = server;
