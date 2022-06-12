CONF_DIR="$(PWD)/docs"
BUILD_DIR="$(PWD)/docs/_generated"
GIT_DOC="docs/dist"
OUT_DIR="$(PWD)/$(GIT_DOC)"

.PHONY: docs
docs: clean
	novella -d $(CONF_DIR) -b $(BUILD_DIR) --site-dir $(OUT_DIR)

.PHONY: serve_docs
serve_docs:
	novella -d $(CONF_DIR) -r --serve

publish_docs:
	git subtree push --prefix $(GIT_DOC) origin gh-pages

clean:
	if [ -d "${BUILD_DIR}" ]; then \
        rm -r ${BUILD_DIR}; \
    fi \