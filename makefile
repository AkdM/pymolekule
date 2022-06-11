.PHONY: docs
docs:
	novella -d "$(PWD)/docs" -b "$(PWD)/docs/_build" --site-dir "$(PWD)/documentation"

.PHONY: serve_docs
serve_docs:
	novella -d "$(PWD)/docs" -r --serve