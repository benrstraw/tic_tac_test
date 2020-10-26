const url = new URL(window.location.href);
const game = url.searchParams.get("g");
const ws = new WebSocket("ws://tac.benrstraw.xyz/" + (game ? game : ""));

ws.onerror = function(error) {
	console.error(error);
};

ws.onclose = function() {
	console.log("Closed!");
	document.getElementById('connection').innerText = "Disconnected";
};

ws.onopen = function() {
	console.log("Opened!");
	document.getElementById('connection').innerText = "Connected";
};

ws.onmessage = function(event) {
	let data = JSON.parse(event.data);
	handle(data);
};

function makeMove(id) {
	const index = id.slice(-1);
	send(parseInt(index));
}

function send(cmd) {
	const out = JSON.stringify(cmd);
	console.log(out);
	ws.send(out);
}


function updateBoard(data) {
	for(let i=0; i<data.board.length; i++) {

		const elem = document.getElementById("in" + i);

		if(data.board[i] === 'X') {
			elem.classList.add("p1")
		}
		else if(data.board[i] === 'O'){
			elem.classList.add("p2")
		}
		else {
			elem.classList.remove("p1");
			elem.classList.remove("p2");
		}

		elem.innerHTML = data.board[i];
	}
}

function handle(data) {
	console.log(data);
	document.getElementById("specCount").innerText = data.specs;
	document.getElementById("myPiece").innerText = data.you;

	if (data.you === 'X')
	{
		if(data.playero) {
			document.getElementById("opConn").innerText = "True";
		}
		else {
			document.getElementById("opConn").innerText = "False";
		}
	}
	else if(data.you === 'O'){
		if(data.playerx) {
			document.getElementById("opConn").innerText = "True";
		}
		else {
			document.getElementById("opConn").innerText = "False";
		}
	}
	else if(!data.you) {
		document.getElementById("opConnTr").hidden = true;
	}

	// This is always in a superposition of either '' or null depending on
	// the average spin on all of the constituent electrons in Ben's brain
	if(!data.you){
		document.getElementById("myPiece").innerText = "Spectator";
	}

	updateBoard(data);

	if(data.winner === "tie") {
		//FUCKING AIDS. FUCK YOU JS
		setTimeout(function() { alert('Tie Game!'); }, 50);
		document.getElementById("winner").innerText = "Tie Game";
	}
	else if(data.winner) {
		//FUCKING AIDS. FUCK YOU JS
		setTimeout(function() { alert(data.winner + " Won!"); }, 50);
		document.getElementById("winner").innerText = data.winner;
	}
	else {
		if(data.turn === data.you) {
			document.getElementById("currTurn").innerText = "Yours";
		}
		else if(!data.turn){
			document.getElementById("currTurn").innerText = "No Player";
		}
		else {
			document.getElementById("currTurn").innerText = data.turn + "'s turn";
		}

		document.getElementById("winner").innerText = "No Winner";
	}

}

function test(str) {
	send({ 'test': str });
}
