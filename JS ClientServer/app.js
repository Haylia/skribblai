"use strict";

//Set up express
const express = require("express");
const app = express();

//Setup socket.io
const server = require("http").Server(app);
const io = require("socket.io")(server);

const request = require("request"); // added request
let players = new Map();
let playersToSockets = new Map();
let socketsToPlayers = new Map();
let nextPlayerNumber = 0;
let state = { state: 0, countdown: 45 };
let timer = null;
let round = 0;
let prompts_ready = false;
let chains = new Map();

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

// URL of the backend API ( might not need this)
const BACKEND_ENDPOINT = process.env.BACKEND || "http://localhost:8181";
//const axios = require("axios").create({ baseURL: BACKEND_ENDPOINT });

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

//Handle registration                     ( The below function works without the url, u can use this for easy login or register)
// function handleRegister(credentials, socket) {
//   let username = credentials.username;
//   let password = credentials.password;

//   handleJoin(socket, username);
//   updateAll();
// }
function handleRegister(credentials, socket) {
  let username = credentials.username;
  let password = credentials.password;

  var payload = {
    username: username,
    password: password,
  };

  const options = {
    url: "https://skribblai-ajwl1g21-2324.azurewebsites.net/player/register?code=DrcOLAi96xZ9HD0oqVw7JiqarME0TmHUauR7d0CCBBLLAzFu9ejEQg==",
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    json: payload,
  };

  request(options, function (err, res, body) {
    if (err) {
      console.error(err);
      socket.emit("fail", "Error during registration");
      return;
    }

    console.log(res.statusCode, body);

    if (body && body.result === true) {
      handleJoin(socket, username);
      updateAll();
      socket.emit("register", {
        result: true,
        message: "Registration successful",
      });
    } else {
      socket.emit("fail", body ? body.msg : "Registration failed");
    }
  });
}
// handle login   ( The below function works without the url, u can use this for easy login or register)
// function handleLogin(credentials, socket) {
//   let username = credentials.username;
//   let password = credentials.password;

//   handleJoin(socket, username);
//   updateAll()
// }
function handleLogin(credentials, socket) {
  let username = credentials.username;
  let password = credentials.password;

  var payload = {
    username: username,
    password: password,
  };

  const options = {
    url: "https://skribblai-ajwl1g21-2324.azurewebsites.net/player/login?code=uBl1SXjrNTQDs3BvcjRUHqHP8OKKaBpjpWn-3BdvRP0XAzFuDMtlwQ==",
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    json: payload,
  };

  request(options, function (err, res, body) {
    if (err) {
      console.error(err);
      socket.emit("fail", "Error during login");
      return;
    }

    console.log(res.statusCode, body);

    if (body && body.result === true) {
      handleJoin(socket, username);
      updateAll();
      socket.emit("login", {
        result: true,
        message: "Login successful",
      });
    } else {
      socket.emit("fail",  body ? body.msg : "Login failed");
    }
  });
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

  if (action == "start" && state.state == 0 && round == 0) {
    nextRound();
  } else if (action == "previous_chain") {
    for (let [player, socket] of playersToSockets) {
      socket.emit("previous_chain");
    }
  } else if (action == "next_chain") {
    for (let [player, socket] of playersToSockets) {
      socket.emit("next_chain");
    }
  }
  
  else {
    console.log("Unknown admin action: " + action);
  }
}

//Start the game
function nextRound() {
  if (round < 3) {
    console.log("Round starting");
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
    round++;
  } else {
    endGame();
  }
}

//Game tick
function tickGame() {
  if (state.countdown > 1) {
    state.countdown--;
    console.log("Tick " + state.countdown);
  } else {
    clearInterval(timer);
    timer = null;
    endRound();
  }
  updateAll();
}

//End round -> 2
function endRound() {
  state.state = 2;
  state.countdown = 45;
  console.log("Round ending");
  timer = setInterval(() => {
    waitForPrompts();
  }, 1000);
}

//End game -> 3
function endGame() {
  state.state = 3;
  console.log("Game ending");
  announce("Game over");
  updateAll();
  results();
}

// Sends the chains to each player ready for displaying
function results() {
  // turns the Map into something that can be sent over a socket
  let transitMap = JSON.stringify(Array.from(chains));
  for (let [player, socket] of playersToSockets) {
    socket.emit('chain', transitMap);
  }
}

// Sets everything to 0 and puts everyone back to the lobby
function restart() {
  state.state = 0;
  round = 0;
  chains.clear();
  for (let [player, socket] of playersToSockets) {
    socket.emit("restart");
  }
  updateAll();
}

function waitForPrompts() {
  if (prompts_ready) {
    clearInterval(timer);
    timer = null;
    prompts_ready = false;
    for (let [playerNumber, chain] of chains) {
      let promptNumber = round - 1;
      let thePrompt = chain[promptNumber]["thePrompt"];
      let nextPlayer = playerNumber + 1;
      if (nextPlayer > players.size) {
        nextPlayer = 1;
      }
      let socket = playersToSockets.get(nextPlayer);
      socket.emit("prompt", thePrompt);
    }
    nextRound();
    updateAll();
  } else {
    prompts_ready = true;
    for (let [playerNumber, chain] of chains) {
      if (chain.length != round) {
        prompts_ready = false;
      }
    }
  }
}

const { google } = require('googleapis');
const auth = new google.auth.GoogleAuth({
  keyFile: 'skribblai-5b2bb317849c.json',  // Replace with path to your key file
  scopes: ['https://www.googleapis.com/auth/cloud-platform'],
});

async function getAccessToken() {
  const accessToken = await auth.getAccessToken();
  return accessToken;
}

function getPrompt(base64image, accessToken, playerNumber) {
  // Calls the API to the AI to get the prompt for the image
  var payload = {
    "instances": [
    {
        "image": {
            "bytesBase64Encoded": base64image.split(',')[1]
        }
    }
    ],
    "parameters": {
      "sampleCount": 1,
      "language": "en"
    }
  };
  
  const options = {
    url: "https://europe-west2-aiplatform.googleapis.com/v1/projects/skribblai/locations/europe-west2/publishers/google/models/imagetext:predict",
    method: "POST",
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json; charset=utf-8'
    },
    json: payload,
  };

  request(options, function (err, res, body) {
    if (err) {
      console.error(err);
      socket.emit("fail", "Error during login");
      return;
    }
    try{
      let thePrompt = body['predictions'][0];
      // create the chain
      let pair = {
        image: base64image,
        thePrompt: thePrompt,
      }
      // check if the user chain exists in the chains
      if (chains.has(playerNumber)) {
        let chain = chains.get(playerNumber);
        chain.push(pair);
      } else {
        let chain = new Array();
        chain.push(pair);
        chains.set(playerNumber, chain);
      }
    } catch (e) {
      let pair = {
        image: base64image,
        thePrompt: "No image found",
      }
      // check if the user chain exists in the chains
      if (chains.has(playerNumber)) {
        let chain = chains.get(playerNumber);
        chain.push(pair);
      } else {
        let chain = new Array();
        chain.push(pair);
        chains.set(playerNumber, chain);
      }
    }
  });
}

function send_to_database(image, username, thePrompt) {
  // stores the image and the prompt into the database
  const url = "https://skribblai-ajwl1g21-2324.azurewebsites.net/submit/drawing?code=Wn0EL94ahQmDHf1d2WriBxNYcgYGlIbc6TV7mEvsn4DOAzFuAmfrzg==";
  var payload = {
    username: username,
    roundnum: round,
    image: image,
    prompt: thePrompt
  }

  const options = {
    url: url,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    json: payload,
  };

  request(options, function (err, res, body) {
    if (err) {
      console.error(err);
      socket.emit("fail", "Error during login");
      return;
    }

    console.log(res.statusCode, body);

    if (body && body.result === true) {
      console.log("Submitted image");
      
    } else {
      socket.emit("fail", body ? body.msg : "login failed");
    }
  })
}

//Chat message
function handleChat(player, message) {
  console.log("Handling chat: " + message + " from player " + player);
  announce(player + ": " + message);
}

//Handles players or audience memmbers quitting the game
function handleQuit(socket) {
  if (socketsToPlayers.has(socket)) {
    nextPlayerNumber = 1;
    const player = socketsToPlayers.get(socket);

    players.delete(player);
    socketsToPlayers.delete(socket);
    playersToSockets.delete(player);
    
    let tempPlayers = new Map();
    let tempSocketsToPlayers = new Map();
    let tempPlayersToSockets = new Map();
    
    for (let [playerNumber, player] of players) {
      player.name = nextPlayerNumber;
      tempPlayers.set(nextPlayerNumber, player);
      let playerSocket = playersToSockets.get(playerNumber);
      tempPlayersToSockets.set(nextPlayerNumber, playerSocket);
      tempSocketsToPlayers.set(playerSocket, nextPlayerNumber);
      nextPlayerNumber++;
    }
    
    players = tempPlayers;
    socketsToPlayers = tempSocketsToPlayers;
    playersToSockets = tempPlayersToSockets;

    if (players.size == 0) {
      nextPlayerNumber = 0;
    }
    
    console.log(players);
    
    console.log('Handling quit from player ' + player);
  } 
  updateAll();
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
    handleQuit(socket);
  });

  //Handle login
  socket.on("login", (credentials) => {
    handleLogin(credentials, socket);
  });

  //Handle registration
  socket.on("register", (credentials) => {
    handleRegister(credentials, socket);
  });

  //Handle image
  socket.on("image", (base64image) => {
    console.log("Image received");
    let playerNum = socketsToPlayers.get(socket);
    getAccessToken().then(accessToken => getPrompt(base64image, accessToken, playerNum));
  });

  //Handle restart
  socket.on("restart", () => {
    console.log("returning to game lobby");
    restart();
  })
});

//Start server
if (module === require.main) {
  startServer();
}

module.exports = server;
