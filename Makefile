clean:
	find . -name "*.pyc" -delete
	rm -rf ./venv
	rm -rf ./build
	rm -rf ./source/*.zip

build:
	mkdir -p ./build
	rm -rf ./build/*
	virtualenv ./venv -p /usr/local/bin/python3
	./venv/bin/pip3 install -r ./source/requirements.txt
	cd source/
	cp -r ./venv/lib/python*/site-packages/. ./build
	cp -r ./source/. ./build
	cd ./build && zip -r lambda.zip .
	rm -rf ./venv

.PHONY: clean build deploy
