// Search result route module
var express = require('express');
var router = express.Router();

// Controller for search
var search_controller = require('../controllers/searchController');

router.get('/', function (req, res) {
	res.send('Search result page');
})

router.get('/video/:id/term/:query', search_controller.search_result);

module.exports = router;