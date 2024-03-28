log?=INFO
python_cmd=PYTHONPATH=${CURDIR} LOG_LEVEL=$(log) python
#params?=--submit-forms --headless
############################################################
run/demo/langchain: 
	$(python_cmd) egs/langchain/main.py ${params}
.PHONY: run/demo/langchain
############################################################
clean/cache:
	rm -rf .cache .store .tmp
.PHONY: clean/cache
############################################################
