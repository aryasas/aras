import re

with open("ui/src/aras-core/components/ListView.tsx", "r") as f:
    content = f.read()

# Replace <LiveDesignWrapper templateName="ListView"> with <DesignContainer id="list-view-layout" className="flex flex-col h-full w-full">
content = re.sub(r'<LiveDesignWrapper templateName="ListView">.*?(<div key="toolbar" className="w-full">)',
                 r'<DesignContainer id="list-view-layout" className="flex flex-col h-full w-full">\n        <DesignElement id="toolbar" className="w-full">',
                 content, flags=re.DOTALL)

# Replace </div> for toolbar
content = re.sub(r'(savedFilters=\{savedFilters\}\n\s+/>\n\s+)</div>\n\s+\)\n\s+}\n\n\s+if \(section\.id === \'filter-bar\'\) \{\n\s+return section\.visible && isFilterOpen && \(',
                 r'\g<1></DesignElement>\n\n        {isFilterOpen && (\n          <DesignElement id="filter-bar"',
                 content, flags=re.DOTALL)

# Replace filter-bar end
content = re.sub(r'(<button onClick=\{.*?>Apply</button>\n\s+</div>\n\s+)</div>\n\s+\)\n\s+}\n\n\s+if \(section\.id === \'table\'\) \{\n\s+return section\.visible && \(',
                 r'\g<1></DesignElement>\n        )}\n\n        <DesignElement id="table"',
                 content, flags=re.DOTALL)

# Replace table end
content = re.sub(r'(</button>\n\s+<ChevronRight size=\{18\} className="text-\[var\(--aras-muted\)\]" />\n\s+</div>\n\s+</div>\n\s+\)\)\n\s+\)\}\n\s+</div>\n\s+</div>\n\s+\)\}\n\s+)</div>\n\s+\)\n\s+}\n\n\s+if \(section\.id === \'pagination\'\) \{\n\s+return section\.visible && viewMode === \'list\' && \(',
                 r'\g<1></DesignElement>\n\n        {viewMode === \'list\' && (\n          <DesignElement id="pagination"',
                 content, flags=re.DOTALL)

# Replace pagination end and closing
content = re.sub(r'(<button disabled=\{page === totalPages\} onClick=\{.*?><ChevronRight size=\{16\} /></button>\n\s+</div>\n\s+)</div>\n\s+\)\n\s+}\n\s+return null\n\s+\}\)}\n\s+</div>\n\s+\)\n\s+\}\}\n\s+</LiveDesignWrapper>',
                 r'\g<1></DesignElement>\n        )}\n\n      </DesignContainer>',
                 content, flags=re.DOTALL)


with open("ui/src/aras-core/components/ListView.tsx", "w") as f:
    f.write(content)

