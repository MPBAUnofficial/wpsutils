import os
import io

from lxml import etree

XSLT_STRIP_NAMESPACES="""
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
"""

XSLT_STRIP_COMMENTS="""
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:output omit-xml-declaration="yes"/>
    <xsl:strip-space elements="*" />
    <xsl:template match="@*|node()" name="identity">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="comment()"/>
        <xsl:template match="@choice">
            <xsl:value-of select="concat(.,'&#x9;')"/>
        </xsl:template>
    <xsl:template match="question|answer">
    <xsl:call-template name="identity"/>
        <xsl:text>&#xA;</xsl:text>
    </xsl:template>
</xsl:stylesheet>
"""

def url_join(*args):
    """
    Join any arbitrary strings into a forward-slash delimited list.
    Do not strip leading / from first element. 
    """
    if len(args) == 0:
        return ""

    if len(args) == 1:
        return str(args[0])

    else:
        args = [str(arg).replace("\\", "/") for arg in args]

        work = [args[0]]
        for arg in args[1:]:
            if arg.startswith("/"):
                work.append(arg[1:])
            else:
                work.append(arg)

        joined = reduce(os.path.join, work)
        joined = joined.replace("\\", "/")

    return joined[:-1] if joined.endswith("/") else joined

def apply_xslt(xslt, xml_tree):
    xslt_transform = etree.parse(io.ByteIO(xslt))
    transform = etree.XSLT(xslt_transform)
    return transform(xml_tree)

def clear_xml_namespaces(xml_tree):
    return apply_xslt(XSLT_STRIP_NAMESPACES, xml_tree)

def clear_xml_comments(xml_tree):
    return apply_xslt(XSLT_STRIP_COMMENTS, xml_tree)
