
// Return list of search results
exports.search_result = function(req, res) {

 	var pythonShell = require('python-shell');

 	var options = {
		pythonPath: '/usr/local/bin/python3',
 		args:
 		[
 			req.query.term
 		]
 	}

 	pythonShell.run('./controllers/Search.py', options, function (err, data) {
 		if (err) 
			throw err ;
		var values = JSON.parse(data[0]).value;
		// res.send(data)
 		res.render('search', {results: values});
 	});
};

