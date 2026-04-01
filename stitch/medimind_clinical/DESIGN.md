# Design System Strategy: The Clinical Curator

## 1. Overview & Creative North Star
The "Clinical Curator" is the creative north star for this design system. In an industry often defined by sterile, boxy templates or cluttered legacy interfaces, this system introduces **Architectural Serenity**. It rejects the traditional "grid-of-boxes" approach in favor of a high-end editorial layout that prioritizes cognitive ease and emotional reassurance.

To achieve a signature feel, we move away from standard UI patterns by employing:
*   **Intentional Asymmetry:** Breaking the vertical rhythm with staggered content blocks to guide the eye naturally.
*   **Tonal Architecture:** Using color shifts rather than lines to define space.
*   **Editorial Typographic Scale:** Using exaggerated contrast between `display` and `body` styles to create an authoritative, "published" feel.

The goal is to transform healthcare data from "medical records" into "wellness narratives," making high information density feel like a premium, breathable experience.

---

## 2. Color & Surface Philosophy
The palette is rooted in medical precision but executed with a soft, contemporary lens. We avoid the "heavy" feel of traditional healthcare apps by utilizing a light-first approach.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders to section off content.
Boundaries must be defined solely through background color shifts. Use `surface-container-low` sections sitting on a `surface` background to create distinction. This creates a "soft-edge" interface that reduces visual noise and cognitive load.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers, similar to stacked sheets of vellum.
*   **Base:** `surface` (#faf9fc)
*   **Sectioning:** `surface_container_low` (#f4f3f6)
*   **Interactive Cards:** `surface_container_lowest` (#ffffff)
*   **Overlays/Modals:** `surface_bright` (#faf9fc)

### The "Glass & Gradient" Rule
To prevent the UI from feeling flat or "cheap," use Glassmorphism for floating elements (e.g., navigation bars or sticky headers). Apply `surface_container_lowest` at 80% opacity with a `backdrop-blur` of 12px. 

For primary CTAs, do not use a flat hex. Apply a subtle linear gradient: 
`linear-gradient(135deg, primary (#00478d) 0%, primary_container (#005eb8) 100%)`. This adds "visual soul" and a tactile, premium depth.

---

## 3. Typography
We use a dual-sans pairing to balance clinical authority with modern accessibility.

*   **Header Font (Manrope):** Chosen for its geometric clarity and high-end editorial feel. It commands attention without being aggressive.
*   **UI Font (Inter):** The workhorse. Optimized for legibility on low-end displays, its tall x-height ensures medical terminology is readable at any size.

### The Hierarchy of Trust
*   **Display (Display-LG/MD):** Used for "Key Health Metrics" or "Welcome States." These should feel cinematic and spacious.
*   **Headlines (Headline-SM):** Use for section titles. Pair with `primary` color to anchor the page.
*   **Body (Body-MD):** The primary reading weight. Use `on_surface_variant` (#424752) for long-form text to reduce eye strain compared to pure black.
*   **Labels (Label-MD):** Used for data captions. Always in `on_secondary_container` (#4f6579) to provide a clear tertiary hierarchy.

---

## 4. Elevation & Depth
In this system, depth is a function of light and layering, not shadows.

*   **The Layering Principle:** Stacking is the primary tool for hierarchy. A `surface_container_lowest` card placed on a `surface_container_low` background creates a natural "lift" that feels integrated into the environment.
*   **Ambient Shadows:** If a floating state (like a popover) is required, use a "Tinted Ambient Shadow." 
    *   *Spec:* `0px 12px 32px rgba(0, 71, 141, 0.06)` (A primary-tinted shadow feels more natural than grey).
*   **The Ghost Border:** If a container requires definition against an identical background (rare, but possible in high-density data), use a `outline_variant` (#c2c6d4) at **15% opacity**. Never use a 100% opaque border.

---

## 5. Components & Primitive Styling

### Buttons
*   **Primary:** Rounded `md` (0.75rem). Use the signature gradient. Large horizontal padding (`spacing-6`) to ensure a premium, uncrowded feel.
*   **Tertiary:** No background or border. Use `primary` text with an icon. These should feel like "inline actions" rather than heavy UI elements.

### Cards & Data Lists
*   **Prohibition:** Never use divider lines between list items.
*   **Alternative:** Separate items using `spacing-2` of vertical white space or alternating backgrounds between `surface_container_lowest` and `surface_container_low`.
*   **Shape:** All cards must use `rounded-lg` (1rem) to maintain the "Soft Clinical" aesthetic.

### Input Fields
*   **Styling:** Use `surface_container_highest` for the input background with no border. On focus, transition the background to `surface_container_lowest` and add a 1px `primary` ghost border (20% opacity).
*   **Tone:** Labels should be `label-md` and always visible. Never use placeholder text as a substitute for a label.

### Specialized Components
*   **The "Metric Micro-Card":** For vitals (Heart rate, etc.), use a compact `surface_container_lowest` card with a `surface_variant` icon background to highlight the data point without visual clutter.
*   **The Progress Vellum:** For patient goals, use a wide, thin progress bar using `primary_fixed` as the track and `primary` as the indicator.

---

## 6. Do's & Don'ts

### Do
*   **Do** embrace white space. If a layout feels "full," increase the spacing between sections by one step on the scale (e.g., from `spacing-8` to `spacing-10`).
*   **Do** use icons from a consistent set (e.g., Lucide) at a `20px` or `24px` size to maintain a "Strong Iconography" presence.
*   **Do** use `secondary_container` for neutral background elements to keep the "Medical Blue" theme consistent even in non-primary areas.

### Don't
*   **Don't** use pure black (#000000) for text. Use `on_surface` (#1a1c1e) to keep the tone "Friendly Clinical."
*   **Don't** use purple or heavy dark modes. This system is designed to feel like a "bright, clean clinic" at 10 AM.
*   **Don't** use sharp corners. Every interaction point should have a minimum radius of `rounded-sm` to avoid looking "aggressive" or "engineered."
*   **Don't** use standard "drop shadows" from software defaults. They break the vellum-layering metaphor.