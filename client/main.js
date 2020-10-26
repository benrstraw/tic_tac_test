const url = new URL(window.location.href);
const game = url.searchParams.get("g");
const ws = new WebSocket("ws://tac.benrstraw.xyz/" + game);

ws.onerror = function(error) {
	console.error(error);
};

ws.onclose = function() {
	console.log("Closed!");
};

ws.onopen = function() {
	console.log("Opened!");
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

function updateBoard(boardData) {
	for(let i=0; i<boardData.length; i++) {
		document.getElementById("in" + i).innerHTML = boardData[i];
	}
}

function handle(data) {
	console.log(data);
	document.getElementById("myPiece").innerText = data.you;

	// This is always in a superposition of either '' or null depending on
	// the average spin on all of the constituent electrons in Ben's brain
	if(!data.you){
		document.getElementById("myPiece").innerText = "Spectator";
	}

	updateBoard(data.board);

	if(data.winner === "tie") {
		//FUCKING AIDS. FUCK YOU JS
		setTimeout(function() { alert('Tie Game!'); }, 1);
		document.getElementById("winner").innerText = "Tie Game";
	}
	else if(data.winner) {
		//FUCKING AIDS. FUCK YOU JS
		setTimeout(function() { alert(data.winner + " Won!"); }, 1);
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
