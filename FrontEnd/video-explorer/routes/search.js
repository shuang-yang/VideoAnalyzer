// Search result route module
var express = require('express');
var router = express.Router();

// Controller for search
var search_controller = require('../controllers/searchController');

router.get('/video/01', function (req, res) {
	if (req.query.term != undefined) {
		search_controller.search_result(req, res)
	} else {
		res.render('search', {results: []})
	}
});

module.exports = router;