var ws = new WebSocket("ws://tac.benrstraw.xyz")

ws.onerror = function(error) {
	console.error(error);
};

ws.onclose = function() {
	console.log("Opened!");
};

ws.onopen = function() {
	console.log("Closed!");
};

ws.onmessage = function(event) {
	data = JSON.parse(event.data);
	handle(data);
};

function send(cmd) {
	var out = JSON.stringify(cmd);
	console.log(out);
	ws.send(out);
}

function handle(data) {
	console.log(data);
}

function test(str) {
	send({ 'test': str });
}