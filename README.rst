.. image:: images/startup_job_scraping.min.png
    :width: 200

=================

This repository provides a few classes to search for startup websites and subsequently scrape them for relevant jobs.
The top-level procedure follows the general pattern:

Search repository website(s) [1]_ for startup's websites > search startup website for job page > search job page for job keywords


Dependencies
============

1. beautifulsoup4 4.7.1
2. selenium 3.141.0
	

Functionalities of startupscraper
=================================

Basic example of scraping for startup jobs with default values::

    from startupscraper.scraper import StartupList
	
    startuplist = StartupList()
    startuplist.find_startups(names=['startupranking'], depth=3)
    startuplist.startup_urls.append('https://lyst.com')
    startuplist.create_startups()
    startuplist.scrape_startups()
    startuplist.save_results('startup_scraping_results.csv')

More particularly:

* .find_startups() : Finds startup urls from a repository.
* .create_startups() : Initializes a Startup.
* .scrape_startups() : Scrapes a Startup for its job page and keyword(s) on these job page.
* .save_results() : Exports hits to a .csv file.


To do
=====

* Add more repositories, e.g. https://data.startups.be/actors

.. [1] Only one repository's procedure has been implemented, i.e. https://startupranking.com/