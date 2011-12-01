#!/usr/bin/env python
import re
import urllib2
from contextlib import closing
import sys

def getHrefs(html):
    hrefs = re.findall(r'href="[^"]*.py"',html) + re.findall(r'href="[^"]*.in"',html)
    return hrefs

def getURLs(html):
    hrefs = getHrefs(html)
    return [s[6:][:-1] for s in hrefs]
    
def pullFiles(html):
    urls = getURLs(html)
    
    while urls:
        passed = []
        for url in urls:
            pyfile = url.rpartition('/')[2]
            print 'getting',pyfile
            try:
                with closing(urllib2.urlopen(url, timeout=120)) as page:
                    data = page.read()
            except KeyboardInterrupt:
                return
            except:
                print 'passed on',pyfile
                passed.append(url)
            else:
                with open('RefCompiler/'+pyfile,'w') as f:
                    f.write(data)
        urls = passed


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            html=f.read()
        pullFiles(html)
