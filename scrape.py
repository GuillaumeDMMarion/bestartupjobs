from startupscraper.scraper import StartupList

def scrape():
  startuplist = StartupList()
  startuplist.locate_startups(names=['startupranking'], depth=3)
  startuplist.create_startups()
  startuplist.scrape_startups()
  return startuplist

startuplist = scrape()
startuplist.save_results('results.csv')