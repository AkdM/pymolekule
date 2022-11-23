CONF_DIR="$(PWD)/docs"
BUILD_DIR="$(PWD)/docs/_generated"
GIT_DOC=docs/dist
OUT_DIR="$(PWD)/$(GIT_DOC)"

.PHONY: docs
docs: clean build_docs

serve_docs:
	@echo "Serving docs…"
	novella -d $(CONF_DIR) -r --serve

build_docs:
	@echo "Building docs…"
	novella -d $(CONF_DIR) -b $(BUILD_DIR) --site-dir $(OUT_DIR)

publish_docs: docs
	@echo "Publishing docs…"
	git subtree push --prefix $(GIT_DOC) origin gh-pages

clean:
	@echo "Cleaning…"
	if [ -d "${BUILD_DIR}" ]; then \
        rm -r ${BUILD_DIR}; \
    fi \