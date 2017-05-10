# Contributing to RAPD

1. [Getting Involved](#getting-involved)
2. [Questions and Discussion](#questions-and-discussion)
3. [How To Report Bugs](#how-to-report-bugs)
4. [How to Contribute Code](#how-to-contribute-code)

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

### How to Contribute Code

### CLA
Please sign our Contributor License Agreement (CLA) before sending pull requests. For any code changes to be accepted, the CLA must be signed. It's a quick process, we promise!

For individuals we have a simple click-through form.
For corporations we'll need you to print, sign and one of scan+email, fax or mail the form.

### Credits
Much of this documentation has been cribbed from a number of other open source projects. Thanks to angular-cli, cla-assistant, and many more.
