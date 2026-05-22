with open('ui/src/index.css', 'r') as f:
    content = f.read()

# Target .aras-form-view .bg-white.rounded-3xl blocks
old_form_panels = """.aras-form-view .bg-white.rounded-3xl,
.aras-form-view .bg-white.rounded-2xl,
.aras-form-view .rounded-3xl.border,
.aras-form-view .rounded-2xl.border {
  border-radius: var(--aras-radius) !important;
  box-shadow: none !important;
  border-color: var(--aras-border) !important;
}"""

new_form_panels = """.aras-form-view .bg-white.rounded-3xl,
.aras-form-view .bg-white.rounded-2xl,
.aras-form-view .rounded-3xl.border,
.aras-form-view .rounded-2xl.border {
  background: color-mix(in srgb, var(--aras-panel) 85%, transparent) !important;
  backdrop-filter: blur(16px);
  border-radius: var(--aras-radius) !important;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08) !important;
  border-color: var(--aras-border) !important;
  overflow: hidden !important;
}"""

old_form_header = """.aras-form-view .px-8.py-4 {
  min-height: 52px;
  display: flex;
  align-items: center;
  background-color: #fbfbfb !important;
}"""

new_form_header = """.aras-form-view .px-8.py-4 {
  background: color-mix(in srgb, var(--aras-panel-soft) 50%, transparent) !important;
  padding: calc(1rem * var(--aras-density)) calc(1.25rem * var(--aras-density)) !important;
  border-bottom: 1px solid var(--aras-border) !important;
  display: flex;
  align-items: center;
}"""

old_form_h3 = """.aras-form-view h3 {
  color: var(--aras-text) !important;
  font-size: calc(15px * var(--aras-font-scale)) !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
}"""

new_form_h3 = """.aras-form-view h3 {
  font-size: calc(0.875rem * var(--aras-font-scale)) !important;
  font-weight: 700 !important;
  color: var(--aras-muted) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}"""

old_form_inputs = """.aras-form-view input,
.aras-form-view select,
.aras-form-view textarea {
  background-color: var(--aras-panel) !important;
  border-color: var(--aras-border-strong) !important;
  border-radius: var(--aras-radius) !important;
  color: var(--aras-text) !important;
  box-shadow: none !important;
}"""

new_form_inputs = """.aras-form-view input,
.aras-form-view select,
.aras-form-view textarea {
  background-color: var(--aras-bg-main) !important;
  border-color: var(--aras-border) !important;
  border-radius: var(--aras-radius) !important;
  color: var(--aras-text) !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}"""

old_focus = """.aras-form-view input:focus,
.aras-form-view select:focus,
.aras-form-view textarea:focus,
.aras-list-toolbar input:focus,
.aras-child-table input:focus,
.aras-child-table select:focus {
  border-color: #a8a8a8 !important;
  outline: none !important;
  --tw-ring-color: transparent !important;
  box-shadow: inset 0 0 0 1px #a8a8a8 !important;
}"""

new_focus = """.aras-form-view input:focus,
.aras-form-view select:focus,
.aras-form-view textarea:focus,
.aras-list-toolbar input:focus,
.aras-child-table input:focus,
.aras-child-table select:focus {
  background-color: var(--aras-panel) !important;
  border-color: var(--aras-border-strong) !important;
  outline: none !important;
  --tw-ring-color: transparent !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--aras-accent) 20%, transparent) !important;
}"""

old_list_view_wrapper = """.aras-list-view {
  min-height: calc(100vh - 170px);
}"""

new_list_view_wrapper = """.aras-list-view {
  min-height: calc(100vh - 170px);
}
.aras-list-view > .flex-1.overflow-auto {
  background: color-mix(in srgb, var(--aras-panel) 85%, transparent) !important;
  backdrop-filter: blur(16px);
  border-radius: var(--aras-radius) !important;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08) !important;
  border-color: var(--aras-border) !important;
}"""

content = content.replace(old_form_panels, new_form_panels)
content = content.replace(old_form_header, new_form_header)
content = content.replace(old_form_h3, new_form_h3)
content = content.replace(old_form_inputs, new_form_inputs)
content = content.replace(old_focus, new_focus)
content = content.replace(old_list_view_wrapper, new_list_view_wrapper)

with open('ui/src/index.css', 'w') as f:
    f.write(content)
print("CSS updated!")
