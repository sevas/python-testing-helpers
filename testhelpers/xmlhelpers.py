"""
Helper functions for comparing XML strings.

Notes on XML comparison
-----------------------

Alright alright. What is the deal about this?

One day, a bunch of people gathered into a room a created the XML data format.
I choose to believe that it was done in an afternoon as a bad joke. Don't email me.

For all intents and purposes, XML is a textual representation of hierarchical
data. For instance, here is a description of a world:

  <world><entity>Pokey</entity><entity>Gustavo</entity><world>


Perhaps you think it's not a very good representation of said world, but XML
allows this.

In their folly, they also decided to add nice features like attributes.

.. code:: xml

    <world kind='arctic_circle'><entity type='penguin'>Pokey</entity><entity type='snowman'>MrNutty</entity></world>


Arguably, the previous example could have been written

.. code:: xml

    <world kind='arctic_circle'><entity type='penguin' name='Pokey'></entity><entity type='snowman' name='MrNutty'></entity></world>


And no one would have been able to decide which one was really better. And perhaps
you will think that it is not a very good use of XML again, but it is still
something XML allows. But I digress.

Now this is all nice and well. Anyone is a bit of programming
experience is probably very familiar with this. XML being unfortunately abused,
chances are, you encountered it in the past.

Now here my favourite bit. XML people try to make you believe that XML is human-
readable. Sure enough, you can write things like this:

.. code:: xml

    <world kind='arctic_circle'>
    <entity type='penguin'>Pokey</entity>
    <entity type='snowman'>MrNutty</entity>
    </world>


And indeed, it tends to make things a little better. More *readable*. You might
also go crazy and use indentation:

.. code:: xml

    <world kind='arctic_circle'>
      <entity type='penguin'>Pokey</entity>
      <entity type='snowman'>MrNutty</entity>
    </world>

Neat. Of course anyone who've come accross any non-trivial XML document knows
that the whole "XML is human readable" is a lie, but let's forget about that.

The fundamental problem with this is that, in XML world, every character is
somehow part of the DOM. There are no such things as "whitespaces". Which means
these nice end-of-lines and indentation characters are **part of the content**.

Yes. Exactly, I want to throw up too. It means that, from the XML point of view,
the last two examples are not the same. They don't have the same content.
Because here is what XML sees, in the case of the two last examples:

 <DOM Element: world><DOM Text node u'\n'><DOM Element: entity><DOM Text node u'\n'><DOM Element: entity>
 <DOM Element: world><DOM Text node u'\n\t'><DOM Element: entity><DOM Text node u'\n\t'><DOM Element: entity>


It's even more obvious if we break the second example which, apart from
indentation, appears to show the exact same content:

 <DOM Element: world><DOM Element: entity><DOM Element: entity>


My best guess is that they wanted this:    <Foo>Hello</Foo>
to be different from this:               <Foo>  Hello  </Foo>

Which kind of make sense if what you want to store inside your nodes
are string literals. But in XML, nodes can have child nodes, mixed up with text
nodes. And suddenly the line between what is a text node and what is XML
formatting becomes blurry. And you end up with the worst of both world:
significant, non-normalized, whitespace.

`Some people <http://xmlunit.sourceforge.net/>`_ pretend that it is by design,
but I fail to see the point. Strings are important data types. You should take
care of them.

Obviously, there is no standard way of indenting. Every XML
processing library has its own way of doing "pretty printing". Maybe all these
libraries are doing XML wrong.

And if things were not bad enough, XML people decided that it was up to the
implementation to decide if whitespace was significant or not. Which means XML
produced by a system might not work when fed to another system.

So there you have it. An XML comparison function that lets you decide if
whitespace is significant or not. I guess it was too hard to come up with a
string literal to encode significant whitespace.

Thanks for nothing.


You read until that point, you might also like:

- http://www.xml.com/pub/a/w3j/s3.nelson.html
- http://www.schnada.de/grapt/eriknaggum-xmlrant.html
- http://harmful.cat-v.org/software/xml/

"""

import xml.dom.minidom as minidom

WHITESPACES = ' \t\r\n'


def is_whitespace_node(element):
    # scroll down for interesting trivia about this!
    return element.nodeType == element.TEXT_NODE and element.data.strip(WHITESPACES) == ""


def cmp_nodes(a, b):
    if a.nodeType == b.nodeType:
        if a.nodeType == a.TEXT_NODE:
            return cmp(a.data, b.data)
        else:
            return cmp(a.tagName, b.tagName)
    else:
        return a.nodeType == a.ELEMENT_NODE and 1 or -1


def element_is_equal(a, b, ignore_whitespace=True, with_debug=False):
    if with_debug:
        print("{} VS {}".format(a.tagName, b.tagName))

    if a.tagName != b.tagName:
        if with_debug:
            print("{} != {}".format(a.tagName, b.tagName))
        return False
    if sorted(a.attributes.items()) != sorted(b.attributes.items()):
        if with_debug:
            print("{} != {}".format(a.attributes.items(), b.attributes.items()))
        return False

    a_childNodes = sorted(a.childNodes, cmp=cmp_nodes)
    b_childNodes = sorted(b.childNodes, cmp=cmp_nodes)

    if ignore_whitespace:
        # see module documentation to understand what's the deal about this
        a_childNodes = [n for n in a_childNodes if not is_whitespace_node(n)]
        b_childNodes = [n for n in b_childNodes if not is_whitespace_node(n)]

    if with_debug:
        print(a_childNodes)
        print(b_childNodes)

    if len(a_childNodes) != len(b_childNodes):
        if with_debug:
            print("[#children:{}]{} != {}".format(a.tagName, len(a.childNodes), len(b.childNodes)))
        return False

    for ac, bc in zip(a_childNodes, b_childNodes):
        if ac.nodeType != bc.nodeType:
            if with_debug:
                print("[nodetype] {} != {}".format(ac.nodeType, bc.nodeType))
            return False

        if ac.nodeType == ac.TEXT_NODE:
            left, right = ac.data, bc.data
            if with_debug:
                print("Text: {} VS {}".format(repr(left), repr(right)))

            if ignore_whitespace:
                left = left.strip(WHITESPACES)
                right = right.strip(WHITESPACES)

            if left and right and left != right:
                if with_debug:
                    print("[data:{}] {} != {}".format(a.tagName, [ac.data], [bc.data]))
                return False
            else:
                return True
        if ac.nodeType == ac.ELEMENT_NODE and not element_is_equal(ac, bc, ignore_whitespace, with_debug):
            return False
    return True


def xml_equal(xml_str1, xml_str2, ignore_whitespace=True, with_debug=False):
    """Test that two xml strings are equal.

    Adapted from this Stack Overflow answer: http://stackoverflow.com/a/321941/40056

    Parameters
    ----------
    xml_str1 : string
    xml_str2 : string
    ignore_whitespace: boolean
        Indicates whether the comparison should ignore leading and trailing
        whitespaces in text nodes. Default is True
    with_debug : boolean
        Print useful debug info to know what caused the xml strings to be
        classified as different.

    Examples
    --------

    >>> xml_equal("<Foo>val</Foo>", "<Foo>val</Foo>")
    True

    >>> xml_equal("<Foo>val</Foo>", "\\n  <Foo>val</Foo>")
    True

    >>> xml_equal("<Foo>\\n\\t\\tval\\n\\t</Foo>", "\\n\\t<Foo>\\n\\t\\tval\\n\\t</Foo>")
    True

    >>> xml_equal("<Foo>val</Foo>", "<Bar>val</Bar>")
    False

    >>> xml_equal("<Foo a='2'>val</Foo>", "<Foo>val</Foo>")
    False

    >>> xml_equal("<Foo a='2' b='3'>val</Foo>", "<Foo a='2' b='2'>val</Foo>")
    False

    >>> xml_equal("<Foo a='2' b='3'>val</Foo>", "<Foo b='3' a='2'>val</Foo>")
    True

    >>> xml_equal("<ROOT><Foo a='2' b='3'>val</Foo></ROOT>", "<ROOT>\\n\\t<Foo b='3' a='2'>val</Foo>\\n</ROOT>")
    True

    >>> xml_equal("<ROOT><Foo a='2' b='3'>val</Foo></ROOT>", "<ROOT>\\n\\t<Foo b='3' a='2'>val</Foo>\\n</ROOT>", ignore_whitespace=False)
    False

    >>> xml_equal("<root><Foo>val</Foo><Bar>hello</Bar></root>", "<root><Bar>hello</Bar><Foo>val</Foo></root>")
    True
    """
    da, db = minidom.parseString(xml_str1), minidom.parseString(xml_str2)
    return element_is_equal(da.documentElement, db.documentElement, ignore_whitespace, with_debug)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
