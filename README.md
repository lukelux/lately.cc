lately.cc
=========
Sync Day One data into Jekyll Blog on the fly

Day One (http://dayoneapp.com) by Bloom Built is an OSX/iOS-centric journaling app with elegantly designed interface. It provides users with awesome journal writing experience from the device of choice. While Day One has no official public API, its data stored in Dropbox can be accessed through Dropbox Core API.

Lately.cc is a simple collection of Python scripts (for now) that actively listens to change stream from Day One's Dropbox, and generate Jekyll blog on the fly. Photo images are stored in ```img```, and journal entries are stored as markdowns in ```_posts``` directory. Users get to choose which entries are published by choosing the entry to be *Starred*. A starred entry that is published can also be removed after the user *Unstars* the entry.

Use of ```longpoll_delta()``` and ```delta()``` Dropbox API enables Lately.cc to listens to change stream in efficient manner without overloading the Dropbox nodes. Changes are applied as they happen from the app (1-2 seconds). 

