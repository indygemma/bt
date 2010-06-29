"""
Behaviour Tree implementation.

behaviour control:
==================
sequence
selector

decorators:
===========
identity
cache
inverse

later to implement:
===================
parallel
"""
from lxml import etree

class SequenceException(Exception):
    pass

class UnknownTagException(Exception):
    pass

class NonExistentBlackboardEntry(Exception):
    pass

class Sequence:
    def __init__(self, children=[]):
        self.children   = children
        self.blackboard = {}

    def __getitem__(self, name):
        return self.blackboard[name]

    def __call__(self, blackboard={}):
        self.blackboard.update(blackboard)
        result = None
        for child in self.children:
            result = child(self.blackboard)
            if not result:
                raise SequenceException("Non-True result found with: %s" % child.name)
        return result

class Selector:
    def __init__(self, children=[]):
        self.children = children
        self.blackboard = {}

    def __call__(self, blackboard={}):
        self.blackboard.update(blackboard)
        for child in self.children:
            try:
                result = child(self.blackboard)
                if result:
                    return result
            except SequenceException, e:
                continue


class Decorator:
    """ applies some logic on a single child (either action or subtree) """
    def __init__(self, name, decorate, child):
        self.name     = name
        self.decorate = decorate
        self.child    = child

    def __call__(self, blackboard):
        # if the action as an "out" attribute, overwrite value for it
        result = self.decorate(self.child(blackboard))
        if self.child.arg_out:
            blackboard[self.child.arg_out] = result
        return result

class Action:
    def __init__(self, name, f, body=None, arg_in=None, arg_out=None, **kwargs):
        self.name = name
        self.f = f
        self.arg_in = arg_in
        self.arg_out = arg_out
        self.body    = body
        self.kwargs  = kwargs

    def __call__(self, blackboard):
        args = []
        if self.body:
            args.append(self.body)
        if self.arg_in:
            for arg_in in self.arg_in:
                if arg_in in self.kwargs:
                    # user-override of specific keyword arguments, specified in action part
                    args.append(self.kwargs[arg_in])
                    del self.kwargs[arg_in]
                elif not arg_in in blackboard:
                    raise NonExistentBlackboardEntry("%s is not on the blackboard" % self.arg_in)
                else:
                    args.append(blackboard[arg_in])
            result = self.f(*args, **self.kwargs)
        else:
            result = self.f(*args, **self.kwargs)
        blackboard[self.arg_out] = result
        return result

def parseElement(bt, el):
    if hasattr(el.tag, "__call__"):
        # this is a callable, maybe comment? ignore
        return None
    tag = el.tag.lower()
    children = []
    for child in el.getchildren():
        item = parseElement(bt, child)
        if item:
            children.append(item)
    if tag == "sequence":
        return Sequence(children)
    if tag == "selector":
        return Selector(children)
    elif bt.hasDecorator(tag):
        return Decorator(tag, bt.getDecorator(tag), children[-1])
    elif bt.hasAction(tag):
        body = None or el.text
        arg_in  = [] if not "in"  in el.keys() else el.get("in").split(",")
        arg_out = None if not "out" in el.keys() else el.get("out")
        if "in" in el.attrib:
            del el.attrib["in"]
        if "out" in el.attrib:
            del el.attrib["out"]
        return Action(tag, bt.getAction(tag), body=body, arg_in=arg_in, arg_out=arg_out, **el.attrib)
    else:
        raise UnknownTagException("Unknown tag: %s" % tag)

class BehaviourTree:
    def __init__(self):
        self.decorators = {}
        self.actions    = {}
        self.trees      = {}
        self.blackboard = {}

    def registerDecorator(self, name, f):
        self.decorators[name] = f
    
    def hasDecorator(self, name):
        return name in self.decorators
    
    def getDecorator(self, name):
        return self.decorators[name]

    def registerAction(self, name, f):
        self.actions[name] = f
    
    def hasAction(self, name):
        return name in self.actions
    
    def getAction(self, name):
        return self.actions[name]

    def parseXML(self, xml_string):
        tree = etree.fromstring(xml_string)
        for child in tree.getchildren():
            if "name" in child.keys():
                self.trees[child.get("name")] = parseElement(self, child)
            else:
                raise Exception("'name' attribute required for %s" % child.tag)
    
    def hasTree(self, name):
        return name in self.trees

    def call(self, name, *args, **kwargs):
        self.trees[name].blackboard.update(kwargs)
        return self.trees[name]()

