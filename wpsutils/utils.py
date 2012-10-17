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

def clear_xml_namespaces(xml_tree):
    xslt = etree.parse(io.BytesIO(XSLT_STRIP_NAMESPACES))
    transform = etree.XSLT(xslt)
    return transform(xml_tree)

a = """
def cache(func, time):
    \"\"\"
    Create a cached function wich keeps values
    stored for a fixed amount of time.
    \"\"\"
    import os
    cache = {}
    def inner(**kwargs):
        if kwargs in cache.keys():
"""
