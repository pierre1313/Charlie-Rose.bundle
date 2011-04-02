import re, string

CR_PREFIX       = '/video/charlierose'
CR_ROOT         = 'http://www.charlierose.com'
CR_TOPICS       = 'http://www.charlierose.com/topic/all'
CR_GUESTS       = 'http://www.charlierose.com/guest/grid'
CR_RECENT_CLIPS = 'http://www.charlierose.com/search/recent_clips/'
CR_COLLECTIONS  = 'http://www.charlierose.com/rss/collections/'
CR_SEARCH       = 'http://www.charlierose.com/search/?text='
CR_NAMESPACE    = {'m':'http://search.yahoo.com/mrss/'}

CACHE_INTERVAL = 3600*8

ART = 'art-default.jpg'
ICON = 'icon-default.png'
NAME = 'Charlie Rose'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(CR_PREFIX, MainMenu, NAME, ICON, ART)
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("PanelStream", viewMode="PanelStream", mediaType="items")
  
  MediaContainer.title1 = 'Charlie Rose'
  MediaContainer.content = 'Items'
  MediaContainer.art = R(ART)
  MediaContainer.viewGroup = "List"
  DirectoryItem.thumb = R(ICON)
  
  HTTP.CacheTime = CACHE_INTERVAL

####################################################################################################
def UpdateCache():
   HTTP.Request(CR_ROOT)
   HTTP.Request(CR_TOPICS)
   HTTP.Request(CR_GUESTS+'/popular?pagenum=1')
   HTTP.Request(CR_GUESTS+'/recent?pagenum=1')
   HTTP.Request(CR_RECENT_CLIPS+'?pagenum=1')
   GetCollectionsMenu(ItemInfoRecord())
  
####################################################################################################
def MainMenu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(GetTopicMenu,       title="Recent Clips"), url=CR_RECENT_CLIPS))
  dir.Append(Function(DirectoryItem(GetGuestsMenu,      title="Guests")))
  dir.Append(Function(DirectoryItem(GetTopicsMenu,      title="Topics")))
  dir.Append(Function(DirectoryItem(GetCollectionsMenu, title="Collections")))
  dir.Append(Function(SearchDirectoryItem(Search,       title=L("Search..."), prompt=L("Search for Interviews"), thumb=R('search.png'))))
  return dir

####################################################################################################
def GetGuestsMenu(sender):
  dir = MediaContainer(title2='Guests')
  dir.Append(Function(DirectoryItem(GetGuestListAlphabet, title="By Last Name")))
  dir.Append(Function(DirectoryItem(GetGuestList, title="Most Popular"), url='popular?'))
  dir.Append(Function(DirectoryItem(GetGuestList, title="Most Recent"), url='recent?'))
  return dir
  
####################################################################################################
def GetGuestListAlphabet(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  for ch in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']:
      dir.Append(Function(DirectoryItem(GetGuestList, title=ch), url='all?letter='+ch+'&'))
  return dir

####################################################################################################
def GetGuestList(sender, url, page=1):
  dir = MediaContainer(viewGroup='PanelStream', title2=sender.itemTitle, replaceParent=(page>1))
  xml = HTML.ElementFromURL(CR_GUESTS+"/"+url+"pagenum="+str(page))
  for guest in xml.xpath('//li[@class="guests"]'):
    key = guest.find('a').get('href')
    title = guest.xpath('div/h5/a')[0].text
    num_appearances = guest.xpath('div/p/span')[0].text.strip()
    most_recent = guest.xpath('div/p')[1].text.strip()
    try: thumb = CR_ROOT + guest.xpath('a/img')[0].get('src')
    except: thumb = None
    dir.Append(Function(DirectoryItem(GetGuestAppearances, title=title, thumb=thumb, subtitle="%s (%s)" % (num_appearances, most_recent)), url=key))
    
  try: numPages = int(re.findall('[0-9]+', xml.xpath('//span[@class="page-select"]/a')[-2].get('href'))[0])
  except: numPages = 1
  if page < numPages:
    dir.Append(Function(DirectoryItem(GetGuestList, "More..."), url=url, page=page+1))
    
  dir.title2 = dir.title2 + " (%d of %d)" % (page, numPages)
  return dir

####################################################################################################
def GetGuestAppearances(sender, url):
  return GetTopicMenu(sender, CR_ROOT+url, extraClass=' guest', useSummary=True)

####################################################################################################
def GetTopicsMenu(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  for topic in HTML.ElementFromURL(CR_TOPICS).xpath('//table[@class="view-list"]/tbody/tr'):
    rows = topic.xpath('td')
    title = rows[0].find('a').text
    subtitle = rows[1].text
    dir.Append(Function(DirectoryItem(GetTopicMenu, title=title, subtitle=subtitle), url=CR_ROOT+rows[0].find('a').get('href')))
  return dir

####################################################################################################
def GetTopicMenu(sender, url, page=1, extraClass='', useSummary=False):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle, replaceParent=(page>1))
  xml = HTML.ElementFromURL(url+'?pagenum=%d' % page)
  for item in xml.xpath('//ol[@class="medallion%s"]/li' % extraClass):
    try: img = CR_ROOT + item.xpath('a/img')[0].get('src').replace('140x90', '460x345')
    except: img = None
    try:
      key = item.xpath('a')[0].get('href')
      title = item.xpath('a/img')[0].get('alt').strip()
      subtitle = item.xpath('div/p/abbr')[0].text
      rating = str((len(item.xpath('*/*/span')[0].text.split('\n'))-2)*2)
      duration = int(item.xpath('dl/dd')[0].text.split()[0])*60*1000
      if useSummary:
        summary = ''.join(xml.xpath('//div[@id="content-rail"]')[0].itertext()).strip()
      else:
        summary = None
      dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=subtitle, summary=summary, thumb=img, duration=duration, rating=rating), url=key))
    except:
      pass
      
  try: numPages = int(re.findall('[0-9]+', xml.xpath('//span[@class="page-select"]/a')[-2].get('href'))[0])
  except: numPages = 1
    
  if page < numPages:
    dir.Append(Function(DirectoryItem(GetTopicMenu, "More..."), url=url, page=page+1, extraClass=extraClass, useSummary=useSummary))
    
  if len(dir) == 0:
    if url.index(CR_SEARCH) != -1:
      return MessageContainer("Search", "No items found.")
    else:
      return MessageContainer("No items available", "They are either not available yet or have been deleted.")
  
  return dir

####################################################################################################
def GetCollectionsMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  
  for topic in XML.ElementFromURL(CR_COLLECTIONS).xpath('//item'):
    title = topic.find('title').text
    desc = topic.find('description').text
    link = topic.find('link').text.strip()
    xml = HTML.ElementFromURL(link)
    thumb = CR_ROOT+xml.xpath("id('content-rail')/img")[0].get('src')
    dir.Append(Function(DirectoryItem(GetTopicMenu, title=title, thumb=thumb, summary=desc), url=link))
    
  return dir

####################################################################################################
def Search(sender, query, page=1):
  return GetTopicMenu(sender, url=CR_SEARCH+query.replace(' ','+'))

####################################################################################################
def PlayVideo(sender, url):
  page = HTTP.Request(CR_ROOT+url).content
  url_pattern = re.compile('"url":"([^&]+.flv)')
  url = url_pattern.search(page)
  if url != None:
    url = url.group(1)
    return Redirect(url) 
  else:
    link_pattern = re.compile('<link rel=\"video_src\" href=\"http://www.charlierose.com/swf/CRGoogleVideo.swf\?docId=([^"]+)"')
    link = link_pattern.search(page)
    if link != None:
      link = link.group(1)
    docID = link.split('%3A')
    xml = XML.ElementFromURL("http://video.google.com/videofeed?fgvns=1&fai=1&docid=%s&begin=%s&len=%s&hl=undefined" % (docID[0], docID[1], docID[2]))
    url = xml.xpath('//m:content[@type="video/x-flv"]', namespaces=CR_NAMESPACE)[0].get('url')   
  return Redirect(url)
