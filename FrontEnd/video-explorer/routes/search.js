// Search result route module
var express = require('express');
var router = express.Router();

// Controller for search
var search_controller = require('../controllers/searchController');

router.get('/', function (req, res) {
	res.render('search', { title: 'Search Result', result: ["car", "lol"]});
})

router.get('/video/:id/term/:query', search_controller.search_result);

// function search_result(req, res) {
// 	var spawn = require('child_process').spawn;
//     var process = spawn('python', ['Search.py',
//         req.params.query
//     ]);
//     // res.send("Finished handling" + req.params.query);
//     process.stdout.on('data', function (data) {
//         res.send(data.toString());
//         // res.send("Finished handling" + req.params.query);
//     });
// }

module.exports = router;