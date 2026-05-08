<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>XML Sitemap</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
            color: #333;
            margin: 0;
            padding: 2rem;
          }
          a {
            color: #0051C3;
            text-decoration: none;
          }
          a:hover {
            text-decoration: underline;
          }
          h1 {
            margin: 0 0 1rem 0;
            color: #1d1d1d;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-radius: 6px;
          }
          th {
            background: #f8f9fa;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid #eee;
          }
          td {
            padding: 1rem;
            border-bottom: 1px solid #eee;
          }
          tr:last-child td {
            border-bottom: none;
          }
          .url-cell {
            word-break: break-all;
          }
        </style>
      </head>
      <body>
        <h1>XML Sitemap</h1>
        <table>
          <tr>
            <th>URL</th>
          </tr>
          <xsl:for-each select="sitemap:urlset/sitemap:url">
            <tr>
              <td class="url-cell">
                <a href="{sitemap:loc}">
                  <xsl:value-of select="sitemap:loc"/>
                </a>
              </td>
            </tr>
          </xsl:for-each>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet> 