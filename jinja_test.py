import jinja2
import bt
import json
from lxml import etree
import crawler

xml = """
<tree>
    <sequence name="test">
            <xpath in="content" out="list">
                <![CDATA[
                //ul/li
                ]]>
            </xpath>
            <json>
                <jinja in="list">
                    [
                    {% for item in list %}
                        {{ item.text }} {% if not loop.last %},{% endif %}
                    {% endfor %}
                    ]
                </jinja>
            </json>
    </sequence>
    <sequence name="test2">
        <json-list in="content"
                   elements="//ul/li"
                   element="./text()" />
    </sequence>
    <sequence name="reddit">
        <crawl in="url" out="content" 
               url="http://www.reddit.com" />
        <json-list in="content"
                   elements="//a[@class='title ']"
                   element ='"{{ item.text | escape }}"' />
    </sequence>

    <sequence name="dp-sites">
        <crawl in="url" out="content"
               url="http://forums.digitalpoint.com/forumdisplay.php?f=52" />
        <json-list in="content" out="auctions"
                   elements="//a[contains(@id, 'thread_title')]"
                   element ='{"url":"http://forums.digitalpoint.com/{{ item.get("href").split("?") }}", "title":"{{ item.text | escape }}"}' />
    </sequence>

    <sequence name="dp-sites2">
        <crawl in="url" out="content"
               url="http://forums.digitalpoint.com/forumdisplay.php?f=52" />
        <json-list in="content" out="auctions"
                   elements="//a[contains(@id, 'thread_title')]"
                   element ='{"url":"http://forums.digitalpoint.com/{{ item.get("href") }}", "title":"{{ item.text | escape }}"}' />
        <!-- <json-for-each in="auctions" out="item"> -->
            <crawl in="url" out="content"
                   url="{{ item.url }}" />
            <sequence>
                <xpath in="content" xpath="//url"   out="site_url" />
                <xpath in="content" xpath="//price" out="site_price" />
                <!-- <istrue in="site_url" /> -->
                <!-- <istrue in="site_price" /> -->
                <!-- <sitecheck in="site_url" out="site_report" /> -->
            </sequence>
        <!-- </json-for-each> -->
    </sequence>
</tree>
"""

def xpath_action(body, content):
    html_parser = etree.HTMLParser()
    html = etree.fromstring(content, html_parser)
    return html.xpath(body)

def jinja_action(body, items, **kwargs):
    template = jinja2.Template(body)
    return template.render(list=items)

def json_list2(content, **kwargs):
    stylesheet = """
    <xsl:stylesheet version="1.0"
                    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
        <xsl:output method="text" />
        <xsl:template match="/">[<xsl:for-each select="%(elements_xpath)s"><xsl:value-of select="%(element_xpath)s" /><xsl:if test="not(position() = last())">,</xsl:if></xsl:for-each>]</xsl:template>
        </xsl:stylesheet>
    """ % {'elements_xpath':kwargs['elements'],
           'element_xpath' :kwargs['element']}
    html_parser = etree.HTMLParser()
    html = etree.fromstring(content, html_parser)
    xslt = etree.fromstring(stylesheet)
    style = etree.XSLT(xslt)
    return style(html)

def json_list(content, **kwargs):
    template = """[{%% for item in items %%}%(element)s{%% if not loop.last %%},{%% endif %%}{%% endfor %%}]""" % {
        'element' : kwargs['element']
    }
    
    html_parser = etree.HTMLParser()
    html        = etree.fromstring(content, html_parser)
    t           = jinja2.Template(template)
    items       = html.xpath(kwargs["elements"])
    return t.render(items=items)

def crawl(url, **kwargs):
    content, length = crawler.crawl(url)
    return content

def print_decorator(x):
    print x
    return x

tree = bt.BehaviourTree()
tree.registerDecorator("json", lambda x: json.loads(x))
tree.registerAction("xpath", xpath_action)
tree.registerAction("jinja", jinja_action)
tree.registerAction("json-list", json_list)
tree.registerAction("crawl", crawl)
tree.registerDecorator("print", print_decorator)
tree.parseXML(xml)

#
# Example 1: Call test
#
result = tree.call("test", content="""
<ul>
    <li>1</li>
    <li>2</li>
    <li>3</li>
</ul>
""")
print result

#
# Example 2: Call dp-sites
#
#result = tree.call("dp-sites")
#print json.dumps(json.loads(result), indent=4)

#
# Example 3: Call reddit
#
#result = tree.call("reddit")
#print json.dumps(json.loads(result), indent=4)


