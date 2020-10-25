var url = new URL(window.location.href);
var game = url.searchParams.get("g");
var ws = new WebSocket("ws://tac.benrstraw.xyz/" + game)

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
	data = JSON.parse(event.data);

	if(data.winner) {
		console.log(data.winner + " is the winner!");
	} else {
		var board = data.board;
		console.log(board[0] + '|' + board[1] + '|' + board[2]);
		console.log('-----');
		console.log(board[3] + '|' + board[4] + '|' + board[5]);
		console.log('-----');
		console.log(board[6] + '|' + board[7] + '|' + board[8]);
		console.log(data.turn + "'s turn!");
	}
};

function send(cmd) {
	var out = JSON.stringify(cmd);
	console.log(out);
	ws.send(out);
}

function test(str) {
	send({ 'test': str });
}