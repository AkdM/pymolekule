# novella -d "`pwd`/docs" -b "`pwd`/docs/build"
# novella -d "`pwd`/docs" -r --serve

docs: FORCE
	novella -d "`pwd`/docs" -b "`pwd`/docs/build"
serve_docs:
	novella -d "`pwd`/docs" -r --serve

FORCE: