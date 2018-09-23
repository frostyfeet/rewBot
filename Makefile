VENV_NAME=venv

.PHONY: prepare-dev venv build
all: prepare-dev venv build
prepare-dev: 
	sudo apt-get -y install python3.5 python3-pip
	sudo /usr/bin/easy_install virtualenv
	make venv

venv:
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	./$(VENV_NAME)/bin/pip3 install -r requirements.txt

build: 
	sudo cp rewbot_cron /etc/cron.d/rewbot

