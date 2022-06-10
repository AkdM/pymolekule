docs: FORCE
	novella -d "`pwd`/_docs" -b "`pwd`/_docs/_build" --site-dir "`pwd`/docs"
serve_docs:
	novella -d "`pwd`/_docs" -r --serve

FORCE: