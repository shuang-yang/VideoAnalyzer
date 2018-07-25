
// Return list of search results
exports.search_result = function(req, res) {

	// res.send("你好像来到了没有知识的荒原: " + req.params.id + '没有' + req.params.query);
	
	// var spawn = require("child_process").spawn;
 //    var child = spawn('python', ["./Search.py"
 //        // req.params.query
 //    ]);
 //    // res.send("Finished handling " + req.params.query);
 //    child.stdout.on("data", function (data, err) {
 //        // res.send(data.toString());
 //        console.log("data:" + data + " error: " + err );
 //    });
    // res.send("Finished handling " + req.params.query);
 	var pythonShell = require('python-shell');

 	var options = {
		pythonPath: '/usr/local/bin/python3',
 		args:
 		[
 			req.params.query
 		]
 	}

 	pythonShell.run('./controllers/Search.py', options, function (err, data) {
 		if (err) 
 			throw err ;
 		res.send(data);
 	});
};

