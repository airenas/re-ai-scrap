log?=INFO
python_cmd=PYTHONPATH=${CURDIR} LOG_LEVEL=$(log) python
############################################################
run/demo/langchain: 
	$(python_cmd) egs/langchain/main.py
.PHONY: run/demo/langchain
############################################################
clean/cache:
	rm -rf .cache .store .tmp
.PHONY: clean/cache
############################################################
