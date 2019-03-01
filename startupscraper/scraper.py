# Library imports
import re
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException




class Driver(webdriver.Chrome):
  '''
  The Driver is a child class of the selenium.webdriver.Chrome class.
    It allows small alterations to some of the parent methods to suit our needs for this particular scraping challenge.
    More paticularly a repeater for resilient javaScript content is implemented.
  '''
  def __init__(self, driverpath='chromedriver', driveroptions='Default'):
    '''
    We initialize a headless selenium.webdriver.Chrome class.
      Some options are included by default for increased speed (not tested for reproducability).
    '''
    super(Driver, self).__init__(executable_path=driverpath, chrome_options=self.feed_options(keyword_or_options=driveroptions))

  @staticmethod
  def feed_options(keyword_or_options):
    if keyword_or_options=='Default':
      options = webdriver.ChromeOptions()
      options.add_argument('headless')
      options.add_argument('--no-proxy-server')
      options.add_argument("--proxy-server='direct://'")
      options.add_argument("--proxy-bypass-list=*")
      options.add_argument("--log-level=3")
      return options
    elif type(keyword_or_options)==webdriver.ChromeOptions:
      options = keyword_or_options
      return options
    else:
      raise TypeError("One of 'Default' or options of type webdriver.ChromeOptions should be given.")

  def find_element_(self, how, what, retry=1):
    cycle = 1
    while True:
      try:
        element = getattr(self,'find_element_'+how)(what)
        return element
      except NoSuchElementException:
        if cycle==retry:
          return None
        cycle+=1
        pass


class StartupList(list):
  '''
  Class for managing the scraping; Following the order of the methods, the class allows:
    - fetching of startup homepage url's through the use of UrlProvider
    - initialization of Startups based on those url's
    - scraping of all Startups within self (i.e. the list)
    - saving of the resulting hits to a .csv file
  '''
  def __init__(self, driverpath='chromedriver', driveroptions='Default'):
    '''
    The driverpath and driveroptions will be fed to the Driver's initializer.
    The startup_urls and startups lists can be subsequently populated with the available methods.
    '''
    self.driver = Driver(driverpath=driverpath, driveroptions=driveroptions)
    self.startup_urls = []
    self.startups = []
    list.__init__(self,())

  def locate_startups(self, names, depth):
    print("\n"+"Populating startup urls:")
    names = [names] if type(names)==str else names
    for name in names:
      urlprovider = UrlProvider(name=name, depth=depth, driver=self.driver)
      self.startup_urls.extend(urlprovider.get_urls())

  def create_startups(self):
    print("\n"+"Creating startups:")
    try:
      assert len(self.startup_urls)>0
    except AssertionError as e:
      e.args += ("No startup urls from which to create Startups.", "Use self.locate_startups() method.")
      raise
    print("> Step 1 : Initializing Startup objects.")
    for startup_url in tqdm(self.startup_urls):
      startup = Startup(startup_url=startup_url, driver=self.driver)
      #self.startups.append(startup)
      self.append(startup)

  def scrape_startups(self):
    print("\n"+"Scraping startup urls for relevant jobs:")
    print("> Step 1 & 2 : Fetching career page links & finding job keywords.")
    for startup in tqdm(self):
      result = startup.find_jobs(link_texts=['Job','job','Join','join','Career','career'], keywords=['freelance camera operator','data scientist','machine learning','artificial intelligence'], return_results=True)

  def save_results(self, path):
    text_tuples = [(startup.name, dic_key, startup.finds[dic_key]) for startup in self for dic_key in startup.finds]
    text = [','.join([name, keyword, url]) for name, keyword, urls in text_tuples for url in urls]
    print(text)
    with open(path, 'w') as f:
      for line in text:
        f.write(line)
        f.write('\n')

class UrlProvider(object):
  '''
  Class which provides and executes methods for populating a list of starup homepage url's.
    Each method is dependent on the desired repository through the use of _UrlProviderMethods.
    Methods implemented for following repositories:
      - 'https://www.startupranking.com/top/belgium'
    Not implemented yet:
      - 'https://data.startups.be/actors'
  '''
  def __init__(self, name, driver, depth):
    self.name = name
    self.driver = driver
    self.depth = depth

  def names_dic(self):
    names_dic = dict(startupranking='https://www.startupranking.com/top/belgium',
                     startupsbe='https://data.startups.be/actors'
                     )
    return names_dic

  def map_url(self, dic={}):
    names_dic = dict(self.names_dic(), **dic)
    return names_dic[self.name]

  class _UrlProviderMethods(object):
    '''
    Class for providing the appropriate scraping method as a function of the desired repository.
    '''
    def __init__(self):
      pass

    def _get_urls_startupranking(driver, base_url, depth):

      def _tags_from_class(driver, base_url, class_name, tag):
        driver.get(base_url)
        element = driver.find_element_('by_class_name', class_name, retry=1000)
        if element == None:
          raise NoSuchElementException('Did not find the desired second page urls, try increasing retries.')
        element_source = element.get_attribute("innerHTML")
        soup = BeautifulSoup(element_source, 'html.parser')
        tags = soup.find_all(tag)
        return tags

      def _get_secondpage_urls(driver=driver, base_url=base_url, depth=depth):
        print("> Step 1 : Fetching second page urls.")
        secondpage_urls = []
        base_urls = [base_url+'/'+str(pagenr) for pagenr in range(1,1+depth)]
        for base_url in tqdm(base_urls):
          tags = _tags_from_class(driver=driver, base_url=base_url, class_name="ranks", tag="a")
          pattern = 'href\=\"\/[a-z1-9-]*\"\>'
          [secondpage_urls.extend(re.findall(pattern, str(tag))) for tag in tags]
        secondpage_urls = [secondpage_url[7:-2] for secondpage_url in secondpage_urls]
        unique_secondpage_urls = list(set(secondpage_urls))
        return sorted(unique_secondpage_urls)

      def _get_startup_urls(secondpage_urls, limit=None):
        print("> Step 2 : Fetching startup urls.")
        startup_urls = []
        for secondpage_url in tqdm(secondpage_urls[:limit]):
          tags = _tags_from_class(driver=driver, base_url="https://www.startupranking.com/"+secondpage_url, class_name="su-logo", tag="a")
          pattern = 'http\\:\/\/.+\?'
          [startup_urls.extend(re.findall(pattern, str(tag))) for tag in tags]
        startup_urls = [startup_url.replace("?","") for startup_url in startup_urls]
        return startup_urls
      return _get_startup_urls(secondpage_urls=_get_secondpage_urls())

    def _get_urls_startupsbe():
      return []

  def get_urls(self):
    base_url = self.map_url()
    return getattr(self._UrlProviderMethods,'_get_urls_'+self.name)(driver=self.driver, base_url=base_url, depth=self.depth)


class Startup(object):
  def __init__(self, startup_url, driver):
    '''
    Class which provides methods for:
     - finding job pages for a particular homepage url
     - finding keywords on the resulting job pages
    '''
    self.name = self._get_name_from_url(startup_url)
    self.url = startup_url
    self.driver = driver
    self.finds = {}

  def __repr__(self):
    return '<Startup> '+self.name

  def __eq__(self, other):
    return self.name == other

  @staticmethod
  def _get_name_from_url(url):
    name = re.findall("\/.+\.", url)[0].replace("www","").replace("//","").replace(".","")
    return name

  def _get_frontpage_links(self, link_texts, driver):
    self.driver.get(self.url)
    links = []
    for link_text in link_texts:
      element = driver.find_element_('by_partial_link_text', link_text, retry=10)
      links.append(element.get_attribute('href')) if element != None else None
    return links

  def find_jobs(self, link_texts, keywords, return_results=False):
    job_page_links = list(set(self._get_frontpage_links(link_texts=link_texts, driver=self.driver)))
    for job_page_link in job_page_links:
      #job_page_link.click()
      self.driver.get(job_page_link) # Slow!? Try the click() version?
      element = self.driver.find_element_('by_css_selector', 'body', retry=10)
      visible_text = element.text.lower()
      for keyword in keywords:
        is_found = re.findall(keyword, visible_text)
        if is_found:
          try:
            self.finds[keyword].append(job_page_link)
          except KeyError:
            self.finds[keyword] = []
            self.finds[keyword].append(job_page_link)
    if return_results:
      return self.finds.keys()

  def has_job(self):
    at_least_one_find = len(self.finds)>0
    return at_least_one_find