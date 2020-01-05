import re
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException




class Driver(webdriver.Chrome):
  '''
  The Driver class is a child class of the selenium.webdriver.Chrome class. A repeater is implemented to, for example, 
  get through resilient javaScript content.
  '''
  def __init__(self, driverpath='chromedriver', driveroptions='Default'):
    '''
    Args:
      driverpath (str): Either a variable or path pointing to the chromedriver executable.
      driveroptions (str/webdriver.ChromeOptions): Either 'Default' string or webdriver options.
    '''
    super(Driver, self).__init__(executable_path=driverpath,
                                 chrome_options=self._feed_options(keyword_or_options=driveroptions))

  @staticmethod
  def _feed_options(keyword_or_options):
    if keyword_or_options=='Default':
      options = webdriver.ChromeOptions()
      #options.add_argument('headless')
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
    '''
    Args:
      how (str): Suffix to the 'find_element_' string corresponding to a Selenium method.
      what (str): Web element to find.
      retry (int): Number of retries in case of NoSuchElementException error.

    Returns:
      The web element found, or None.
    '''
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
  Class for organizing the scraping objective of all startups; Following the logical order of the methods, the class 
  allows:
    - fetching startup homepage url's through the use of the UrlProvider class
    - initialization of Startup classes based on those urls
    - scraping of those pages for specific keywords with the Startup classes' methods
    - saving the results to a .csv file
  '''
  def __init__(self, driverpath='chromedriver', driveroptions='Default'):
    '''
    Args:
      driverpath (str): Either a variable or path pointing to the chromedriver executable.
      driveroptions (str/webdriver.ChromeOptions): Either 'Default' string or webdriver options.
    '''
    self.driver = Driver(driverpath=driverpath, driveroptions=driveroptions)
    self.startup_urls = []
    list.__init__(self,())

  def find_startups(self, names=['startupranking'], depth=1):
    '''
    Args:
      names (list): List of predefined names of startup-repository webpages. Implemented: 'startupranking'.
      depth (int): Number of pages of the repository to go through.

    Returns:
      None; Appends the discovered startup url's to StartupList.startup_urls.
    '''
    print("\n"+"Populating startup urls:")
    names = [names] if type(names)==str else names
    for name in names:
      urlprovider = UrlProvider(name=name, depth=depth, driver=self.driver)
      self.startup_urls.extend(urlprovider.get_urls())

  def create_startups(self):
    '''
    Returns:
      None; Appends Startup classes to StartupList based on the StartupList.startup_urls.
    '''
    print("\n"+"Creating startups:")
    try:
      assert len(self.startup_urls)>0
    except AssertionError as e:
      e.args += ("No startup urls from which to create Startups.", 
                 "Use self.find_startups() method or add urls manually to StartupList.startup_urls.")
      raise
    print("> Step 1 : Initializing Startup objects.")
    for startup_url in tqdm(self.startup_urls):
      startup = Startup(startup_url=startup_url, driver=self.driver)
      self.append(startup)

  def scrape_startups(self, link_texts=['Job','job','Join','join','Career','career'], keywords=['data scientist',
                      'machine learning','artificial intelligence']):
    '''
    Args:
      link_texts (list): List of potential job page names.
      keywords (list): List of keywords to look for on the job pages found.
    
    Returns:
      None; Appends the scraping results to each Startup class.
    '''
    print("\n"+"Scraping startup urls for relevant jobs:")
    print("> Step 1 & 2 : Fetching career page links & finding job keywords.")
    for startup in tqdm(self):
      result = startup.find_jobs(link_texts=link_texts, keywords=keywords, return_results=True)

  def save_results(self, path='startup_scraping_results.csv'):
    '''
    Args:
      path (str): Path to write the .csv file to.

    Returns:
      None; Writes a .csv file of the results. 
    '''
    text_tuples = [(startup.name, dic_key, startup.finds[dic_key]) for startup in self for dic_key in startup.finds]
    text = [','.join([name, keyword, url]) for name, keyword, urls in text_tuples for url in urls]
    print(text)
    with open(path, 'w') as f:
      for line in text:
        f.write(line)
        f.write('\n')


class Startup(object):
  '''
  Class for organizing the scraping objective for each startup; Following the logical order of the methods, the class 
  allows:
   - finding job pages for a particular startups' homepage url
   - finding keywords on the resulting job pages
  '''

  def __init__(self, startup_url, driver):
    '''
    Args:
      startup_url (str): String of the startups' homepage url.
      driver (selenium.webdriver): The webdriver to use for scraping. 
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
    '''
    Args:
      url (str): String of the homepage url.

    Returns:
      The corresponding startup name.
    '''
    name = re.findall("\/.+\.", url)[0].replace("www","").replace("//","").replace(".","")
    return name

  def _get_frontpage_links(self, link_texts):
    '''
    Args:
      link_texts (list): List of potential job page names.

    Returns:
      Urls to potential job pages.
    '''
    self.driver.get(self.url)
    links = []
    for link_text in link_texts:
      element = self.driver.find_element_('by_partial_link_text', link_text, retry=10)
      links.append(element.get_attribute('href')) if element != None else None
    return links

  def find_jobs(self, link_texts, keywords, return_results=False):
    '''
    Args:
      link_texts (list): List of potential job page names.
      keywords (list): List of keywords to look for on the job pages found.
      return_results (bool): Whether or not to return the results.

    Returns:
      Either None, or keywords and corresponding urls found. 
    '''
    job_page_links = list(filter(None,set(self._get_frontpage_links(link_texts=link_texts))))
    for job_page_link in job_page_links:
      #job_page_link.click()
      self.driver.get(job_page_link) # Slow!? Try the click() alternative?
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
    '''
    Returns:
      Whether or not at least one keyword was found.
    '''
    at_least_one_find = len(self.finds)>0
    return at_least_one_find


class UrlProvider(object):
  '''
  Class which provides and executes methods for populating a list of starup homepage urls.
    Each method is dependent on the desired repository through the use of _UrlProviderMethods.
    Methods implemented for following repositories:
      - 'https://www.startupranking.com/top/belgium'
    Potential next implementation:
      - 'https://data.startups.be/actors'
  '''
  def __init__(self, name, driver, depth):
    '''
    Args:
      name (str): One of the predefined names of startup-repository webpages.
      driver (selenium.webdriver): The webdriver to use for scraping.
      depth (int): Number of pages of the repository to go through.
    '''
    self.name = name
    self.driver = driver
    self.depth = depth

  def names_dic(self):
    '''
    Returns:
      A mapping dictionary of the repository names and corresponding urls.
    '''
    names_dic = dict(startupranking='https://www.startupranking.com/top/belgium',
                     startupsbe='https://data.startups.be/actors'
                     )
    return names_dic

  def map_url(self, dic={}):
    '''
    Returns:
      The repository's url.
    '''
    names_dic = dict(self.names_dic(), **dic)
    return names_dic[self.name]

  def get_urls(self):
    '''
    Returns:
      Startup homepages' urls.
    '''
    base_url = self.map_url()
    return getattr(self._UrlProviderMethods,'_get_urls_'+self.name)(driver=self.driver, base_url=base_url, 
                   depth=self.depth)
    
  class _UrlProviderMethods(object):
    '''
    Container class for providing the appropriate scraping method as a function of the desired repository.
    
    All args:
      base_url (str): repository's first page url.
      depth (int): number of pages to go through.
    
    All returns:
      (list) List of startup homepage url strings.
    '''
    def __init__(self):
      pass

    def _get_urls_startupranking(driver, base_url, depth):

      def _get_startup_urls(secondpage_urls, limit=None):
        print("> Step 2 : Fetching startup urls.")
        startup_urls = []
        for secondpage_url in tqdm(secondpage_urls[:limit]):
          tags = _tags_from_class(driver=driver, base_url="https://www.startupranking.com/"+secondpage_url, 
                                  class_name="su-logo", tag="a")
          pattern = 'http\\:\/\/.+\?'
          [startup_urls.extend(re.findall(pattern, str(tag))) for tag in tags]
        startup_urls = [startup_url.replace("?","") for startup_url in startup_urls]
        return startup_urls

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

      def _tags_from_class(driver, base_url, class_name, tag):
        driver.get(base_url)
        element = driver.find_element_('by_class_name', class_name, retry=1000)
        if element == None:
          raise NoSuchElementException('Did not find the desired second page urls, try increasing retries.')
        element_source = element.get_attribute("innerHTML")
        soup = BeautifulSoup(element_source, 'html.parser')
        tags = soup.find_all(tag)
        return tags

      return _get_startup_urls(secondpage_urls=_get_secondpage_urls())

    def _get_urls_startupsbe():
      return []