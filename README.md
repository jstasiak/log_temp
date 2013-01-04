log_temp
========

Temperature logging Python application. Reads data from ``DS1810/DS18B20/DS18S20`` sensors connected to one-wire bus, puts it in round-robin database and generates graphs.

Requirements
============

* Python >= 2.6
 * pip
 * virtualenv
* digitemp

Fedora
------

    sudo yum install python digitemp python-setuptools
    sudo easy_install virtualenv pip
    
Running
=======

I recommend creating an virtualenv to run this project. In project directory execute:

    virtualenv --distribute env

Then we can install project-specific requirements into virtualenv:

    ./env/bin/pip install -r requirements.txt

In case of ``python-rrdtool`` complaining about missing system packages please consult [python-rrdtool readme](https://github.com/pbanaszkiewicz/python-rrdtool/blob/master/README.rst), install them and repeat requirements installation.

In project directory there's ``default_config.json`` file which contains default configuration (shocking). You can copy it to ``config.json`` and customize it (if you don't do that, it will be created by ``log_temp.py`` script on it's first run).

Things that you can customize include:

* ``port`` - serial port which is used by ``digitemp`` to read data from one-wire bus
* ``sensors_names`` - sensors human-friendly names (mapping, sensor id -> name)
* ``graphs`` - specify start times of generated graphs (end time is always current time), must be ``rrdtool`` compatible (consult [rrdtool AT-STYLE TIME SPECIFICATION](http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html))
* ``databases_path`` - path to directory to store database files
* ``graphs_path`` - path to directory to store generated graphs

You run the application like this:

    sudo ./env/bin/python log_temp.py [LOOP_DELAY]
    
It will loop and do read/save/generate graphs cycle every ``LOOP_DELAY`` seconds. If you skip ``LOOP_DELAY``, the application will run once and quit.

License
=======

BSD, take it and use it
