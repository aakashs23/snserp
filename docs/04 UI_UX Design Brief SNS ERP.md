# **Sri Naga Sai ERP – UI/UX Design Brief (Version 1\)**

## **Purpose**

This document defines the visual identity, design system, interaction patterns, and user experience guidelines for Sri Naga Sai ERP.

The goal is to create a modern, premium, AI-first enterprise application that feels clean, fast, professional, and effortless to use. The UI should inspire confidence when managing financial data and company documents while making AI features feel like a natural part of the workflow.

---

# **1\. Overall Aesthetic Direction**

## **Design Style**

The application should follow a **modern enterprise SaaS** design inspired by Pulze AI.

Characteristics

* Minimal and uncluttered  
* Premium appearance  
* AI-first interface  
* Corporate and trustworthy  
* Elegant use of whitespace  
* Soft gradients used sparingly  
* High information density without feeling crowded  
* Smooth animations and micro-interactions  
* Professional rather than playful

The interface should prioritize clarity, productivity, and speed over decorative elements.

---

# **2\. Design Inspiration**

Primary Inspiration

* Pulze AI (Primary Reference)

Secondary Inspirations

* Linear  
* Notion  
* Vercel Dashboard  
* Stripe Dashboard  
* Supabase Dashboard  
* GitHub  
* Raycast

The final UI should resemble a polished enterprise dashboard rather than a traditional ERP system.

---

# **3\. Color Palette**

## **Primary**

Almond Cream

\#F5EBE0

Used for

* Primary buttons  
* Active navigation  
* Charts  
* Focus states  
* Links

---

## **Secondary**

Dark Espresso Brown

\#3D342E

Used for

* Secondary buttons  
* Icons  
* Borders  
* Labels

---

## **Accent**

Soft Dusty Blue

\#7A90A4

Used for

* Success states  
* Revenue indicators  
* Completed invoices  
* Positive financial metrics

---

## **Warning**

Amber

`#F59E0B`

Used for

* Pending invoices  
* OCR processing  
* Warning messages

---

## **Error**

Red

`#EF4444`

Used for

* Validation errors  
* Failed uploads  
* Delete actions

---

## **Background**

Light Mode

Primary Background

\#FBF8F5

Surface Cards

`#FFFFFF`

Sidebar

\#F5EBE0

---

Dark Mode

Primary Background

`#0F172A`

Cards

`#1E293B`

Sidebar

`#111827`

---

## **Text Colors**

Primary

\#F5EBE0

Secondary

\#3D342E

Muted

\#706259

Dark Mode

Primary

`#F9FAFB`

Secondary

`#CBD5E1`

Muted

`#94A3B8`

---

# **4\. Typography**

Primary Font

**Serif \+ Sans-Serif**

Fallback

* system-ui  
* sans-serif

Reasons

* Excellent readability  
* Modern SaaS appearance  
* Optimized for dashboards  
* Great number alignment  
* Clean at small sizes

---

## **Heading Scale**

H1

40px

Bold

Dashboard Titles

---

H2

32px

Bold

Page Titles

---

H3

24px

Semibold

Section Titles

---

H4

20px

Semibold

Cards

---

Body Large

16px

Medium

---

Body

15px

Regular

---

Small

13px

Regular

---

Caption

12px

Medium

---

Buttons

15px

Semibold

---

# **5\. Component Style**

Overall Feel

Soft and modern.

Corners

* Cards → 16px  
* Buttons → 12px  
* Inputs → 12px  
* Dialogs → 20px  
* Dropdowns → 12px  
* Badges → Fully rounded

---

Borders

Very subtle

`1px`

Neutral Gray

---

Shadows

Soft shadows only.

No heavy Material Design shadows.

Cards should appear elevated but lightweight.

---

Spacing

Generous spacing throughout.

Use an 8-point spacing system.

---

Icons

Lucide Icons

Style

* Outline  
* Minimal  
* Consistent stroke width

---

# **6\. Dark Mode**

The application should fully support both Light Mode and Dark Mode.

Dark Mode is not optional.

Requirements

* Same layout  
* Same hierarchy  
* Charts adapt automatically  
* Code blocks optimized  
* AI chat optimized  
* No pure black backgrounds  
* Maintain consistent contrast ratios

The user's theme preference should persist across sessions.

---

# **7\. Layout System**

Maximum Content Width

Fluid layout

Desktop optimized

---

Sidebar

Collapsible

Auto-hide behavior similar to macOS Finder

Width

Expanded

280px

Collapsed

80px

---

Top Navigation

Sticky

Contains

* Global Search  
* Notifications  
* Theme Toggle  
* User Profile

---

Content Area

Scrollable independently

Cards arranged using responsive CSS Grid

---

# **8\. Key UI Patterns**

## **Dashboard Cards**

Rounded

Shadowed

Interactive

Hover animations

Clickable

---

## **Tables**

Modern enterprise tables

Features

* Sticky header  
* Sort  
* Filter  
* Pagination  
* Row selection  
* Bulk actions

---

## **Forms**

Multi-column layouts

Inline validation

Autosave where appropriate

Clear required fields

---

## **Modals**

Centered

Blurred backdrop

Rounded corners

Smooth animations

---

## **Drawers**

Right-side slide-over panels

Used for

* AI Assistant  
* Upload  
* Quick View  
* Edit Details

---

## **File Upload**

Drag & Drop

Progress indicators

Preview before upload

Multiple files supported

---

## **Search**

Global command-style search

Keyboard shortcut

Ctrl \+ K

Supports

* Documents  
* Invoices  
* Customers  
* AI Search

---

## **AI Assistant**

Persistent floating AI button

Right-side chat drawer

Suggested prompts

Typing animation

Document citations

Conversation history

---

# **9\. Data Visualization**

Charts

Use Recharts.

Chart Types

* Line  
* Area  
* Bar  
* Pie  
* KPI Cards

Charts should emphasize readability over decoration.

Animations should remain subtle.

---

# **10\. Motion & Animations**

Animation Style

Fast

Smooth

Professional

Examples

* Sidebar collapse  
* Modal open  
* Card hover  
* AI typing  
* Loading skeletons  
* Upload progress

Animation Duration

150–250ms

Avoid excessive motion.

---

# **11\. Mobile Responsiveness**

The ERP is desktop-first but fully responsive.

Breakpoints

Desktop

≥1280px

Laptop

1024px

Tablet

768px

Mobile

≤640px

---

Desktop

Full sidebar

Multi-column layouts

Complete dashboards

---

Tablet

Collapsible sidebar

Reduced columns

Touch-friendly controls

---

Mobile

Bottom navigation or hamburger menu

Single-column layout

Stacked cards

Responsive tables with horizontal scrolling

AI Assistant accessible from every screen

---

# **12\. Accessibility**

The application should comply with WCAG 2.1 AA guidelines.

Requirements

* Minimum 4.5:1 contrast ratio  
* Keyboard navigation throughout  
* Focus indicators on interactive elements  
* ARIA labels where appropriate  
* Screen reader compatibility  
* Buttons larger than 44×44px on touch devices  
* Avoid using color alone to communicate status  
* Support browser zoom up to 200% without layout issues

---

# **13\. Design Principles**

Every interface should follow these principles:

* Simplicity before complexity.  
* Consistency across all modules.  
* AI should assist—not overwhelm.  
* Financial information should be immediately readable.  
* Important actions should always be visible.  
* Destructive actions must require confirmation.  
* Minimize clicks for common workflows.  
* Keep layouts predictable and intuitive.  
* Use whitespace to improve comprehension.  
* Prioritize speed, clarity, and trust over visual effects.

---

# **14\. Overall Experience Goal**

Users should feel that Sri Naga Sai ERP is:

* Modern and premium  
* Fast and responsive  
* Easy to learn  
* Trustworthy for financial operations  
* AI-powered without feeling gimmicky  
* Consistent across every module  
* Comparable in quality to leading SaaS platforms while remaining tailored to the workflow of a solar power generation company.

