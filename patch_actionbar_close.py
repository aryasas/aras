import re

with open("ui/src/aras-core/components/ListViewActionBar.tsx", "r") as f:
    content = f.read()

# Replace closing tags in reverse order to ensure we close DesignContainers correctly.
# The layout structure is:
# <DesignContainer id="action-bar-layout">
#   <DesignContainer id="action-bar-top-row">
#     <DesignContainer id="action-bar-left-group">
#     ...
#     </div> (closes left group)
#     ... right group
#   </div> (closes top row)
#   ... mobile actions
# </div> (closes layout)

content = re.sub(r'</DesignElement>\n\s+</div>\n\s+<div className="flex h-10 w-full flex-1 items-center gap-2 rounded-xl border border-\[var\(--aras-border\)\] bg-\[var\(--aras-panel-soft\)\] px-3 text-\[var\(--aras-muted\)\]">',
                 r'</DesignElement>\n        </DesignContainer>\n\n        <div className="flex h-10 w-full flex-1 items-center gap-2 rounded-xl border border-[var(--aras-border)] bg-[var(--aras-panel-soft)] px-3 text-[var(--aras-muted)]">',
                 content)

content = re.sub(r'</button>\n\s+</div>\n\s+</div>\n\s+</div>\n\s+\{/\* Mobile Actions \*/\}',
                 r'</button>\n          </div>\n        </div>\n      </DesignContainer>\n\n      {/* Mobile Actions */}',
                 content)

content = re.sub(r'</div>\n\s+</div>\n\s+\);\n\};\n\nexport default ListViewActionBar;',
                 r'</div>\n      </DesignContainer>\n    </DesignContainer>\n  );\n};\n\nexport default ListViewActionBar;',
                 content)

with open("ui/src/aras-core/components/ListViewActionBar.tsx", "w") as f:
    f.write(content)

