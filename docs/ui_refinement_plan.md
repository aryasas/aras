# Implementation Plan - Premium UI Template Refinement

Refine the Aras Framework styling layers in `ui/src/index.css` to build an extremely premium, dynamic, modern SaaS UI. We will also correct dark-mode styling bugs (such as hardcoded light background colors on input elements in forms), restructure elements for optimal visual balance, and reorganize styling assets to support cross-platform development (including React Native / Expo).

## User Review Required

> [!IMPORTANT]
> **Key Enhancements & Repositioning:**
> 1. **Left-Aligned Main Actions:** Move the primary "Add New" button in `ListToolbar.tsx` to the **left** side (at the start of the toolbar before search). Move the "Save" and form action buttons in `DynamicForm.tsx` to the **left** side of the form header bar next to the Cancel/Back arrow.
> 2. **Neater Form Design:** Refine grid alignments, paddings, section headers, and typography inside forms to make the design clean, readable, and perfectly balanced.
> 3. **Eliminate "aras" from CSS:** Rename all custom CSS variables to use `--app-` (e.g. `--app-accent`) and custom CSS classes to `.app-` (e.g. `.app-form-view`). We will declare alias variables and duplicate class selectors in `index.css` to guarantee 100% backward compatibility with React views without risk of breaking active code.
> 4. **Cross-Platform / Expo Support:** Organize variable design tokens into a clean, unified dictionary in `index.css`. This acts as a single-source-of-truth style scheme that can be directly mapped to React Native style objects or Tailwind configurations for a standalone Expo mobile app.

---

## Proposed Changes

### Front-End Component Repositioning

#### [MODIFY] [ListToolbar.tsx](file:///Users/aras/Dev/aras/ui/src/aras-core/components/ListToolbar.tsx)
- Reposition the `onAdd` ("Add New") button to the far left of the toolbar, so it is the first element, preceding the search input box.

#### [MODIFY] [DynamicForm.tsx](file:///Users/aras/Dev/aras/ui/src/aras-core/components/DynamicForm.tsx)
- Reposition the "Save" button to the far left of the form command bar, directly adjacent to the Cancel (Back arrow) button and the record title.

### Front-End Styling System

#### [MODIFY] [index.css](file:///Users/aras/Dev/aras/ui/src/index.css)
- **Token Renaming**: Refactor variables from `--aras-` to `--app-` (e.g., `--app-accent`, `--app-radius`, `--app-border`). Map the legacy `--aras-` keys to these new tokens for backward compatibility.
- **Class Renaming**: Refactor classes from `.aras-` to `.app-` (e.g., `.app-island`, `.app-form-view`, `.app-form-section`, `.app-section-header`, `.app-list-view`, `.app-list-table`, `.app-list-row`). Keep aliased selectors so both prefixes are fully functional.
- **Cross-Platform Token Dictionary**: Document and structure custom HSL variables cleanly so they can easily be exported to React Native stylesheets or Expo configurations.
- **Form Design Neatness**: Optimize form input heights, add elegant focus animations, refine group titles, and adjust section spacing to resemble premium mockups.
- **Login Dark Mode Overrides**: Inject dark-mode style overrides for the login container, input fields, and texts using the obsidian-indigo color palette.

---

## Verification Plan

### Automated / Build Verification
- Run `npm run build` inside `ui/` to ensure the CSS imports compile cleanly without errors or warnings.

### Manual Verification
- Verify that "Add New" button in list view, and "Save" button in form view are correctly positioned on the left.
- Verify the layout and aesthetic appeal of forms and login view in both light and dark modes.
