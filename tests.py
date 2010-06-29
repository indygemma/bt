import unittest
import bt
from lxml import etree
try:
    import json
except:
    import simplejson as json

class BTTest(unittest.TestCase):
    def testTrueSequence(self):
        tree = bt.BehaviourTree()
        tree.registerAction("return-true", lambda: True)
        tree.parseXML("""
            <tree>
                <sequence name="test">
                    <return-true />
                </sequence>
            </tree>
        """)
        self.assertEquals(tree.call("test"), True)
    
    def testSequenceWithBlackboard(self):
        tree = bt.BehaviourTree()
        tree.registerAction("return-true", lambda: True)
        tree.registerAction("pass-through", lambda x: x)
        tree.parseXML("""
            <tree>
                <sequence name="test">
                    <return-true out="result" />
                    <!-- this is a comment -->
                    <pass-through in="result" out="result" />
                </sequence>
            </tree>
        """)
        self.assertEquals(tree.call("test"), True)
    
    def testUnknownTag(self):
        tree = bt.BehaviourTree()
        xml  = """
            <tree>
                <sequence name="test">
                    <lololol /> <!-- this is an unknown tag -->
                </sequence>
            </tree>
        """
        self.assertRaises(bt.UnknownTagException, tree.parseXML, xml)
    
    def testActionsWithSingleInput(self):
        tree = bt.BehaviourTree()
        tree.registerAction("identity", lambda x: x)
        tree.parseXML("""
            <tree>
                <sequence name="test">
                    <identity in="whatever" />
                </sequence>
            </tree>
        """)
        self.assertEquals(tree.call("test", whatever=5), 5)

    def testActionsWithDoubleInput(self):
        xml = """
            <tree>
                <sequence name="test">
                    <add in="a,b" />
                </sequence>
            </tree>
        """
        tree = bt.BehaviourTree()
        tree.registerAction("add", lambda a,b: a+b)
        tree.parseXML(xml)
        self.assertEquals(tree.call("test", a=2, b=5), 7)
        self.assertEquals(tree.call("test", a=10, b=10), 20)
    
    def testActionsWithDecorator(self):
        xml = """
        <tree>
            <sequence name="test">
                <double>
                    <identity in="x" />
                </double>
            </sequence>
        </tree>
        """
        tree = bt.BehaviourTree()
        tree.registerAction("identity", lambda x: x)
        tree.registerDecorator("double", lambda x: x * 2)
        tree.parseXML(xml)
        self.assertEquals(tree.call("test", x=5), 10)
        self.assertEquals(tree.call("test", x=10), 20)

    def testAddition(self):
        xml = """
        <tree>
            <sequence name="addition">
                <double>
                    <add in="a,b" out="result" />
                </double>
                <print in="result" />
            </sequence>
        </tree>
        """
        tree = bt.BehaviourTree()
        
        def print_decorator(result):
            # hypothetical: print result
            return result
        
        def add_action(a,b):
            return a + b

        tree = bt.BehaviourTree()
        tree.registerDecorator("double", lambda x: x * 2)
        tree.registerAction("print",  print_decorator)
        tree.registerAction("add", add_action)
        tree.parseXML(xml)
        self.assertEquals(tree.hasDecorator("double"), True)
        self.assertEquals(tree.hasAction("print"), True)
        self.assertEquals(tree.hasAction("add"), True)
        self.assertEquals(tree.hasTree("addition"), True)
        self.assertEquals(tree.hasTree("division"), False)
        self.assertEquals(tree.call("addition", a=1, b=2), 6)
        self.assertEquals(tree.call("addition", a=1, b=3), 8)

    def testSelector(self):
        xml = """
        <tree>
            <selector name="test">
                <sequence>
                    <istrue in="as_email" />
                    <send-email />
                </sequence>
                <send-sms />
            </selector>
        </tree>
        """
        tree = bt.BehaviourTree()
        tree.registerAction("istrue", lambda x: x == True)
        tree.registerAction("send-email", lambda: "sending email...")
        tree.registerAction("send-sms", lambda: "sending sms...")
        tree.parseXML(xml)
        self.assertEquals(tree.call("test", as_email=True), "sending email...")
        self.assertEquals(tree.call("test", as_email=False), "sending sms...")

    def testActionWithContent(self):
        xml = """
        <tree>
            <sequence name="test">
                <json>
                    <xslt in="content">
                        <![CDATA[
                        <xsl:stylesheet version="1.0"
                                        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
                            <xsl:output method="text" />
                            <xsl:template match="/">[<xsl:for-each select="//ul/li"><xsl:value-of select="./text()" /><xsl:if test="not(position() = last())">,</xsl:if></xsl:for-each>]</xsl:template>
                        </xsl:stylesheet>
                        ]]>
                    </xslt>
                </json>
            </sequence>
        </tree>
        """
        tree = bt.BehaviourTree()
        
        def transformXSLT(body, content):
            html_parser = etree.HTMLParser()
            html = etree.fromstring(content, html_parser)
            xsl = etree.fromstring(body)
            style = etree.XSLT(xsl)
            return style.tostring(style.apply(html))
        
        tree.registerAction("xslt", transformXSLT)
        tree.registerDecorator("json", lambda x: json.loads(x))
        tree.parseXML(xml)
        self.assertEquals(tree.call("test", content="""
            <ul>
                <li>1</li>
                <li>2</li>
                <li>3</li>
            </ul>
        """), [1,2,3])


if __name__ == '__main__':
    unittest.main()

