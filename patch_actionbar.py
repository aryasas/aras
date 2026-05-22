import re

with open("ui/src/aras-core/components/ListViewActionBar.tsx", "r") as f:
    content = f.read()

# Replace <div className="aras-list-action-bar glass-panel island mb-4 flex flex-col gap-3 p-3">
content = re.sub(r'<div className="aras-list-action-bar glass-panel island mb-4 flex flex-col gap-3 p-3">',
                 r'<DesignContainer id="action-bar-layout" className="aras-list-action-bar glass-panel island mb-4 flex flex-col gap-3 p-3">',
                 content)

# Replace <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
content = re.sub(r'<div className="flex flex-col gap-3 lg:flex-row lg:items-center">',
                 r'<DesignContainer id="action-bar-top-row" className="flex flex-col gap-3 lg:flex-row lg:items-center">',
                 content)

# The first child is <div className="flex shrink-0 items-center gap-2">
content = re.sub(r'<div className="flex shrink-0 items-center gap-2">',
                 r'<DesignContainer id="action-bar-left-group" className="flex shrink-0 items-center gap-2">',
                 content)

# Wrap "Add New" button
content = re.sub(r'<button\n\s+type="button"\n\s+onClick=\{onAdd\}\n\s+className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-\[var\(--aras-button\)\] px-5 text-sm font-extrabold text-\[var\(--aras-button-text\)\] transition-all hover:brightness-110 active:scale-\[0.98\]"\n\s+>\n\s+<Plus size=\{17\} />\n\s+Add New\n\s+</button>',
                 r'<DesignElement id="btn-add-new" tagName="button" onClick={onAdd} className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-[var(--aras-button)] px-5 text-sm font-extrabold text-[var(--aras-button-text)] transition-all hover:brightness-110 active:scale-[0.98]"><Plus size={17} />Add New</DesignElement>',
                 content)

# Title
content = re.sub(r'<h1 className="hidden text-xl font-black text-\[var\(--aras-text\)\] lg:block">',
                 r'<DesignElement id="action-bar-title" tagName="h1" className="hidden text-xl font-black text-[var(--aras-text)] lg:block">',
                 content)
content = re.sub(r'</h1\>',
                 r'</DesignElement>',
                 content)

with open("ui/src/aras-core/components/ListViewActionBar.tsx", "w") as f:
    f.write(content)

