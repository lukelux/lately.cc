lately.cc
=========
Sync Day One data into Jekyll Blog on the fly

Day One (http://dayoneapp.com) by Bloom Built is an OSX/iOS-centric journaling app with elegantly designed interface. It provides users with awesome journal writing experience from the device of choice. While Day One has no official public API, its data stored in Dropbox can be accessed through Dropbox Core API.

Lately.cc is a simple collection of Python scripts (for now) that actively listens to change stream from a user's Dropbox (that Day One app writes to), and generate [Jekyll](http://jekyllrb.com/) blog on the fly. Photo images are stored in ```img```, and journal entries are stored as markdowns in ```_posts``` directory. Users get to choose which entries are published by choosing the entry to be *Starred*. A starred entry that is published can also be removed after the user *Unstars* the entry.

Use of ```longpoll_delta()``` and ```delta()``` Dropbox API enables Lately.cc to listen to change stream in efficient manner without overloading the Dropbox nodes. Changes are applied as they happen from the app (1-2 seconds). There are dozens of DayOne export scripts on Github, but they are intended to be used as one time CLI tool. Lately.cc aims to become a service which users can run over a long period of time -- as long as life time of blog itself.

Installation
------------
Download and install [Dropbox Python SDK](https://www.dropbox.com/developers/core/sdks/python)
```bash
# download, unzip, and install
curl -LO https://www.dropbox.com/developers/downloads/sdks/core/python/dropbox-python-sdk-2.2.0.zip
unzip dropbox-python-sdk-2.2.0.zip
cd dropbox-python-sdk-2.2.0 && sudo python setup.py install
```

Lately.cc works with [Jekyll](http://jekyllrb.com/) and [Jinja2](http://jinja.pocoo.org/docs/dev/)
```bash
# prerequisites
gem install jekyll
pip install jinja2
```

Finally clone Lately source
```bash
# simply clone this source
git clone git@github.com:eungyu/lately.cc.git
```

Configuration
-------------
Run the setup script, 
```bash
cd lately.cc
python setup.py
```
The script will run through a dialogue and ask a few questions. The ```basepath``` is the path where your Jekyll directory is setup (simply press enter and it defaults to example app predefined), and ```access_token``` is the token generated from your dropbox app (yes, we do also require you to register a developer app from [Dropbox Developer Console](https://www.dropbox.com/developers/apps)).

The setup script will validate the Jekyll directory and also generate necessary config and data directories.

Running
-------
The following will start pumping incremental data to your Jekyll directory.
```bash
cd lately.cc/listener
nohup ./lately.py > /dev/null 2>&1 &
```
After Lately.cc has been started, you can run periodic Jekyll regeneration to update the blog. More proactive regeneration trigger will be implemented in the future.
