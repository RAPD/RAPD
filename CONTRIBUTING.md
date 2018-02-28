# Contributing to RAPD

1. [Getting Involved](#getting-involved)
2. [Questions and Discussion](#questions-and-discussion)
3. [How To Report Bugs](#how-to-report-bugs)
4. [How to Set Up Development Environment](#how-to-set-up-development-environment)

### Getting Involved
It's not always clear in projects what needs to be done, or what the maintainers are willing to let new contributors (i.e. outsiders) do. The RAPD project is designed as a framework for building plugins, so there are many ways to contribute built into the design of the project.

Ways to help:
* Report a bug
* Make a feature request
* Test with a new version of dependent software and make a pull request
* Fix a bug and make a pull request
* Write a wrapper for a detector
* Write a plugin
* Write some documentation

### Questions and Discussion

### Bugs and Issues
* Claim the issue by posting on the [issues](https://github.com/rapd/rapd/issues) thread
* Search [GitHub](https://github.com/rapd/rapd/pulls) for an open or closed PR
  that relates to your submission. You don't want to duplicate effort. Someone should have updated the issue, but check just in case!
* Make your changes in a new git branch that includes the issue number:
  ```shell
  git checkout -b issNNN master
  ```
* Create your patch
* Run the RAPD test suite to make sure your new code passes
* Commit your changes using a quality commit message.
  ```shell
  git commit -a
  ```
* Push your branch to GitHub:
  ```shell
  git push origin issNNN
  ```
* In GitHub, send a pull request to `rapd:master`.
* If we suggest changes then:
  * Make the required updates.
  * Re-run the Angular CLI test suites to ensure tests are still passing.
  * Rebase your branch and force push to your GitHub repository:
  ```shell
  git rebase master -i
  git push -f
  ```
Easy enough...

### Feature Requests

### How to Set Up Development Environment
This is an aggregation of how to do a full install of RAPD, its web application, services, and the underlying programs. Docker is used where possible to simplify things.

* Install [Docker](https://docs.docker.com) - I will leave this to you. You don't have to use Docker, but it simplifies things.

* Run [MongoDB](https://hub.docker.com/_/mongo/) - MongoDB is a document database. _For more see src/services/README.md_
  * Make a directory to store data in (I have used `/Users/frankmurphy/workspace/data/mongo` on my Mac).
  * Start MongoDB on Docker
    ```shell
    docker run -d -p 27017:27017 --name mongo -v /Users/frankmurphy/workspace/data/mongo:/data/db mongo --storageEngine wiredTiger
    ```

* Run [Redis](https://hub.docker.com/_/redis/) - Redis is an in-memory data structure store. _For more see src/services/README.md_
  * Start Redis on Docker
    ```shell
    docker run -d -p 6379:6379 --name redis  redis  redis-server --appendonly yes
    ```

* Install [Node.js](https://nodejs.org/en/) - Node.js is a JavaScript runtime. _For more see install/README.md_
  * Install [NVM](https://github.com/creationix/nvm) Node Version Manager.  
    Easy installation by curl  
    ```
    curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
    ```  
    or wget  
    ```
    wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
    ```
  * Install Node.js. RAPD uses the Long Term Support branch of NodeJS, currently v8.9.4  
    ```
    nvm install v8.9.4
    nvm alias default v8.9.4
    ```

* Install RAPD - This can take a while... _For more see install/README.md_
  * Clone the RAPD repository where you like `git clone https://github.com/RAPD/RAPD.git rapd`  
  * Navigate to rapd/install within your cloned repository
  * Run the install `./install`


* Install [Angular CLI](https://cli.angular.io).
  * Navigate to src/ui within your cloned repository
  * Install Angular CLI and other UI dependencies `./ng_update.sh`  


* Start RAPD REST service - This serves up the data for the user interface. _For more see src/services/README.md_
  * Navigate to src/services/rest within your cloned repository
  * Copy the `example_config.js` to `config.js` and edit it. The example config has settings for MongoDB and Redis to work out of the box with the Docker environment described here.  
  ```javascript
  module.exports = {

    // mongo or ldap
    authenticate_mode: 'mongo',

    // This will be the address cc'ed on admin emails
    admin_email:'fmurphy@anl.gov',

    // can be overidden by process.ENV
    port: 3000,

    // Name for the site
    site: 'NE-CAT',

    // Used for authentication key, etc
    secret: 'mysecret',

    // Connection strings for MongoDB
    control_conn: 'mongodb://mongo:27017/rapd',
    auth_conn: 'mongodb://mongo:27017/rapd',

    // Redis connection info
    redis_connection: {
        host: 'redis',
        port: 6379
      },

    // Where is my LDAP server? Used if authenticate_mode == 'ldap'
    ldap_server: '127.0.0.1',
    // String for LDAP to find your users
    ldap_dn: 'ou=People,dc=ser,dc=aps,dc=anl,dc=gov',

    // Plugin types that show up in the MongoDB
    plugin_types: ['index', 'integrate']
  };
  ```
  * Build and run the RAPD REST service on Docker.
  ```shell
  docker build -t rapd_rest .
  docker run -d --name rapd_rest --link redis:redis --link mongo:mongo -p 3000:3000 rapd_rest
  ```
* Start the DevServer - This builds and serves the RAPD web UI. _For more see install/README.md_
  * Navigate to src/ui/src/app within your cloned repository
  * Copy the `example_site.js` to `site.js` and edit it. The example site has settings to work out of the box with the RAPD REST service setup described here.

    ```javascript
    import { Injectable, OnInit } from '@angular/core';

    @Injectable()
    export class Site implements OnInit {

      //
      // Server info
      //
      public restApiUrl: string = 'http://localhost:3000/api/';
      public websocketUrl: string = 'ws://localhost:3000';

      //
      // Authentication info
      //
      // The type of user id expected - email or username
      public auth_user_type: string = 'email';
      public have_users:boolean = false;

      //
      // UI
      //
      // The name of the site - used in the UI
      public name:string = 'NECAT';
      public site_tags:string[] = ['NECAT-C', 'NECAT-E']

      ngOnInit() {
      }
    }
    ```
  * Navigate to src/ui within your cloned repository
  * Run the DevServer `ng serve`

* Add yourself to the system - 






### CLA
Please sign our Contributor License Agreement (CLA) before sending pull requests. For any code changes to be accepted, the CLA must be signed. It's a quick process, we promise!

For individuals we have a simple click-through form.
For corporations we'll need you to print, sign and one of scan+email, fax or mail the form.

### Credits
Much of this documentation has been cribbed from a number of other open source projects. Thanks to angular-cli, cla-assistant, and many more.
