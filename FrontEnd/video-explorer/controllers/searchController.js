
// Return list of search results
exports.search_result = function(req, res) {
	res.send("你好像来到了没有知识的荒原: " + req.params.id + '没有' + req.params.query);
};