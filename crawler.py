import urllib2
import urlparse
import httplib
import gzip
import StringIO

USER_AGENT = "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)"
PROXY_URL  = None

def use_proxy(url):
    global PROXY_URL
    PROXY_URL = url

def crawl(url, proxy=None):
    if url.endswith("/"):
        url = url[:-1]
    
    request = urllib2.Request(url)
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept-Encoding", "gzip,deflate")
    if PROXY_URL != None:
        opener = urllib2.build_opener(urllib2.ProxyHandler({'http':PROXY_URL}))
    elif proxy != None:
        opener = urllib2.build_opener(urllib2.ProxyHandler({'http':proxy}))
    else:
        opener = urllib2.build_opener()
    data = opener.open(request)        
    opener.close()
    return decompress(data)

def decompress(data):
    encoding = data.info().get("Content-Encoding")
    content = data.read()
    downloaded_content_length = len(content)
    if encoding in ('gzip', 'x-gzip', 'deflate'):
        if encoding == "deflate":
            content = StringIO.StringIO(zlib.decompress(content))
        else:
            content = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(content))
        content = content.read()    
    return content, downloaded_content_length

def getreply(uri):
    # from http://effbot.org/zone/pil-image-size.htm
    # check the uri
    scheme, host, path, params, query, fragment = urlparse.urlparse(uri)
    if not scheme in ("http", "https"):
        raise ValueError("only supports HTTP requests")
    if not path:
        path = "/"
    if params:
        path = path + ";" + params
    if query:
        path = path + "?" + query
    
    # make the http request
    h = httplib.HTTP(host)
    h.putrequest("HEAD", path)
    h.putheader("User-Agent", USER_AGENT)
    h.putheader("Host", host)
    h.endheaders()
    
    status, reply, headers = h.getreply()
    
    # handle redirects
    if status in (301, 302):
        #print scheme, host
        #print status, reply, headers
        #print headers.get("Location")
        next_location = headers.get("Location")
        if not next_location.startswith("http"):
            if next_location[0] == "/":
                next_location = scheme + "://" + host + next_location
            else:
                next_location = scheme + "://" + host + "/" + next_location
        status, reply, headers = getreply(next_location)
    
    h.close()
    return status, reply, headers

def test_getreply(url):
    import socket
    try:
        reply = getreply(url)
        print reply[2]
        print reply[0], reply[1], reply[2].get("Content-Type")
    except socket.gaierror:
        print "DNS ERROR DUDE"

def test_crawl(url):
    content, content_length = crawl(url)
    print content

if __name__ == '__main__':
    #test_crawl("http://www.coesmilsim.com/modules.php?name=Forums&file=viewtopic&t=2378")
    test_getreply("http://www.coesmilsim.com/modules.php?name=Forums&file=viewtopic&t=2378")