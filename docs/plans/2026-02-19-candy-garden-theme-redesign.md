# Candy Garden Theme Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign Explorito with a warm, vibrant "Candy Garden" color palette and kid-friendly UI that works perfectly on mobile.

**Architecture:** CSS-first approach using Tailwind v4 `@theme` block to define a complete design token system in `globals.css`. All hardcoded colors across ~30 component files get replaced with semantic tokens and candy palette utilities. Font swap to Nunito. Mobile bottom navigation added. Touch targets enlarged to 48px minimum.

**Tech Stack:** Tailwind CSS v4, Next.js Google Fonts (Nunito), shadcn/ui components (restyled), CSS custom properties

---

## Color Palette Reference

| Token | Name | Hex | Usage |
|-------|------|-----|-------|
| `--candy-purple` | Vivid Purple | `#7C3AED` | Primary actions, active states |
| `--candy-purple-light` | Soft Lavender | `#EDE9FE` | Backgrounds, highlights |
| `--candy-orange` | Coral Orange | `#F97316` | Gamification, XP, streaks |
| `--candy-orange-light` | Peach | `#FFF7ED` | Warm backgrounds |
| `--candy-green` | Emerald | `#10B981` | Correct answers, completed |
| `--candy-green-light` | Mint | `#D1FAE5` | Success backgrounds |
| `--candy-red` | Strawberry | `#EF4444` | Wrong answers |
| `--candy-red-light` | Rose | `#FEE2E2` | Error backgrounds |
| `--candy-yellow` | Sunshine | `#F59E0B` | Stars, rewards, XP |
| `--candy-yellow-light` | Lemon | `#FEF3C7` | Reward backgrounds |
| `--candy-pink` | Cotton Candy | `#EC4899` | Accents, fun elements |
| `--candy-surface` | Cream | `#FFFBF5` | Page backgrounds |
| `--candy-card` | White | `#FFFFFF` | Cards |
| `--candy-text` | Deep Indigo | `#1E1B4B` | Primary text |
| `--candy-text-muted` | Warm Gray | `#6B7280` | Secondary text |
| `--candy-border` | Soft Lavender | `#E5E1F5` | Borders |

## Font

- **Primary:** Nunito (rounded, friendly, highly legible for kids)
- **Fallback:** system-ui, sans-serif

---

### Task 1: Design System Foundation - globals.css + Font Setup

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/app/layout.tsx`

**Step 1: Replace globals.css with complete Candy Garden design system**

Replace the entire `globals.css` with:

```css
@import "tailwindcss";

:root {
  /* Candy Garden Palette */
  --candy-purple: #7C3AED;
  --candy-purple-light: #EDE9FE;
  --candy-purple-dark: #5B21B6;
  --candy-orange: #F97316;
  --candy-orange-light: #FFF7ED;
  --candy-green: #10B981;
  --candy-green-light: #D1FAE5;
  --candy-red: #EF4444;
  --candy-red-light: #FEE2E2;
  --candy-yellow: #F59E0B;
  --candy-yellow-light: #FEF3C7;
  --candy-pink: #EC4899;
  --candy-pink-light: #FCE7F3;
  --candy-surface: #FFFBF5;
  --candy-card: #FFFFFF;
  --candy-text: #1E1B4B;
  --candy-text-muted: #6B7280;
  --candy-border: #E5E1F5;

  /* shadcn/ui semantic tokens mapped to Candy Garden */
  --background: #FFFBF5;
  --foreground: #1E1B4B;
  --card: #FFFFFF;
  --card-foreground: #1E1B4B;
  --popover: #FFFFFF;
  --popover-foreground: #1E1B4B;
  --primary: #7C3AED;
  --primary-foreground: #FFFFFF;
  --secondary: #EDE9FE;
  --secondary-foreground: #5B21B6;
  --muted: #F5F3FF;
  --muted-foreground: #6B7280;
  --accent: #FFF7ED;
  --accent-foreground: #F97316;
  --destructive: #EF4444;
  --destructive-foreground: #FFFFFF;
  --border: #E5E1F5;
  --input: #E5E1F5;
  --ring: #7C3AED;
  --radius: 1rem;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --font-sans: var(--font-nunito);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);

  /* Candy palette as Tailwind utilities */
  --color-candy-purple: #7C3AED;
  --color-candy-purple-light: #EDE9FE;
  --color-candy-purple-dark: #5B21B6;
  --color-candy-orange: #F97316;
  --color-candy-orange-light: #FFF7ED;
  --color-candy-green: #10B981;
  --color-candy-green-light: #D1FAE5;
  --color-candy-red: #EF4444;
  --color-candy-red-light: #FEE2E2;
  --color-candy-yellow: #F59E0B;
  --color-candy-yellow-light: #FEF3C7;
  --color-candy-pink: #EC4899;
  --color-candy-pink-light: #FCE7F3;
  --color-candy-surface: #FFFBF5;
  --color-candy-text: #1E1B4B;
  --color-candy-text-muted: #6B7280;
  --color-candy-border: #E5E1F5;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: var(--font-nunito), system-ui, sans-serif;
}

/* Candy Garden global animations */
@keyframes candy-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes candy-wiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-3deg); }
  75% { transform: rotate(3deg); }
}

@keyframes candy-pop {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes candy-glow {
  0%, 100% { box-shadow: 0 0 8px rgba(124, 58, 237, 0.3); }
  50% { box-shadow: 0 0 20px rgba(124, 58, 237, 0.5); }
}

@keyframes candy-float {
  0% { transform: translateY(0) scale(1); opacity: 1; }
  100% { transform: translateY(-60px) scale(1.2); opacity: 0; }
}

@keyframes candy-spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes candy-shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-6px); }
  40%, 80% { transform: translateX(6px); }
}

@keyframes confetti-fall {
  0% { transform: translateY(-20px) rotate(0deg); opacity: 1; }
  100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}

@keyframes feedback-slide-up {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Candy utility classes */
.candy-shadow {
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
}

.candy-shadow-lg {
  box-shadow: 0 8px 24px rgba(124, 58, 237, 0.12), 0 2px 6px rgba(0, 0, 0, 0.04);
}

.candy-shadow-glow {
  box-shadow: 0 0 20px rgba(124, 58, 237, 0.2), 0 4px 14px rgba(124, 58, 237, 0.1);
}

/* Scrollbar styling for kids */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--candy-purple-light);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--candy-purple);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--candy-purple-dark);
}
```

**Step 2: Update layout.tsx to use Nunito font**

Replace Geist imports with Nunito:

```tsx
import { Nunito } from "next/font/google";

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
});
```

Update body className to use `nunito.variable` instead of `geistSans.variable geistMono.variable`.

Also change `lang="en"` to `lang="fr"`.

**Step 3: Verify the font renders**

Run: `docker compose restart frontend`
Check: `http://localhost:3005` -- text should render in Nunito (rounded letterforms).

**Step 4: Commit**

```bash
git add frontend/src/app/globals.css frontend/src/app/layout.tsx
git commit -m "feat: add Candy Garden design system with Nunito font and CSS tokens"
```

---

### Task 2: Update shadcn/ui Base Components

**Files:**
- Modify: `frontend/src/components/ui/button.tsx`
- Modify: `frontend/src/components/ui/card.tsx`
- Modify: `frontend/src/components/ui/input.tsx`
- Modify: `frontend/src/components/ui/progress.tsx`
- Modify: `frontend/src/components/ui/dialog.tsx`

**Step 1: Update button.tsx**

Changes:
- `rounded-md` → `rounded-xl` in all variants
- Default size `h-9 px-4 py-2` → `h-11 px-5 py-2.5 text-base`
- Small size `h-8` → `h-9`
- Large size `h-10` → `h-12`
- Icon size `h-9 w-9` → `h-11 w-11`
- Add `font-semibold` to base styles
- Add `transition-all duration-200` and `active:scale-95` for bouncy tap feedback

**Step 2: Update card.tsx**

Changes:
- `rounded-xl` → `rounded-2xl` on Card
- Add `candy-shadow` class alongside existing `shadow` (or replace)

**Step 3: Update input.tsx**

Changes:
- `rounded-md` → `rounded-xl`
- `h-9` → `h-12`
- Add `text-base` for readability on mobile
- Border color already uses `border-input` which maps to our lavender

**Step 4: Update progress.tsx**

Changes:
- `h-2` → `h-3`
- Indicator: add `bg-gradient-to-r from-candy-purple to-candy-pink` as the default look (via overriding `bg-primary`)
- Add `rounded-full` if not already present

**Step 5: Update dialog.tsx**

Changes:
- `sm:rounded-lg` → `rounded-2xl`
- Overlay `bg-black/80` → `bg-black/40` (less scary for kids)

**Step 6: Verify components render**

Run: `docker compose restart frontend`
Navigate to pages using these components and check visual changes.

**Step 7: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: restyle shadcn/ui components for Candy Garden (rounder, larger, kid-friendly)"
```

---

### Task 3: Mobile Navigation - Bottom Tab Bar + Responsive Header

**Files:**
- Create: `frontend/src/components/layout/BottomNav.tsx`
- Modify: `frontend/src/components/layout/Header.tsx`
- Modify: `frontend/src/components/layout/ChildLayout.tsx`

**Step 1: Create BottomNav.tsx**

A fixed bottom navigation bar for mobile screens with 4 tabs: Play, Subjects, Dashboard, Profile. Uses large 48px touch targets. Hidden on `md:` and above.

```tsx
"use client";

import { usePathname, useRouter } from "next/navigation";
import { Gamepad2, BookOpen, LayoutDashboard, User } from "lucide-react";
import { useAuth } from "@/lib/auth";

const tabs = [
  { href: "/play", icon: Gamepad2, label: "Jouer" },
  { href: "/subjects", icon: BookOpen, label: "Matières" },
  { href: "/dashboard", icon: LayoutDashboard, label: "Tableau" },
];

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();

  // Hide for admin pages
  if (pathname.startsWith("/admin")) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-candy-border md:hidden">
      <div className="flex items-center justify-around py-2 px-4 safe-area-bottom">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href || pathname.startsWith(tab.href + "/");
          return (
            <button
              key={tab.href}
              onClick={() => router.push(tab.href)}
              className={`flex flex-col items-center justify-center min-w-[64px] min-h-[48px] rounded-xl transition-all duration-200 ${
                isActive
                  ? "text-candy-purple bg-candy-purple-light scale-105"
                  : "text-candy-text-muted hover:text-candy-purple"
              }`}
            >
              <tab.icon className="h-6 w-6" />
              <span className="text-xs font-semibold mt-0.5">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
```

**Step 2: Update Header.tsx for mobile**

Changes:
- Hide navigation links on mobile (they live in BottomNav now): wrap nav items in `hidden md:flex`
- Logo "Explorito" gets candy styling: `text-candy-purple font-extrabold`
- Keep avatar/logout visible on mobile
- Header background: `bg-white/80 backdrop-blur-sm border-b-2 border-candy-border`
- Impersonation banner: `bg-candy-yellow-light text-candy-text border-b-2 border-candy-yellow`

**Step 3: Update ChildLayout.tsx**

Changes:
- Import and render `<BottomNav />` after `<main>`
- Add `pb-20 md:pb-0` to main content to account for bottom nav on mobile
- Background: `bg-candy-surface min-h-screen`

**Step 4: Verify on mobile viewport**

Run: `docker compose restart frontend`
Open Chrome DevTools, toggle device toolbar, check 375px width. Bottom nav should appear. Header nav items should be hidden.

**Step 5: Commit**

```bash
git add frontend/src/components/layout/
git commit -m "feat: add mobile bottom tab bar and responsive header for Candy Garden"
```

---

### Task 4: Restyle Landing Page + Auth Pages

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/(auth)/login/page.tsx`
- Modify: `frontend/src/app/(auth)/register/page.tsx`

**Step 1: Restyle landing page**

Changes:
- Background: `bg-gradient-to-b from-candy-purple-light via-candy-surface to-candy-orange-light`
- Title: `text-4xl md:text-6xl font-extrabold text-candy-text` with a candy gradient text effect
- Subtitle: `text-lg md:text-xl text-candy-text-muted`
- CTA buttons: large, rounded, candy-colored (primary purple, secondary orange outline)
- Add mascot emoji section: large owl/candy character with bounce animation
- Spinner: `border-candy-purple` instead of `border-primary`

**Step 2: Restyle login page**

Changes:
- Background: `bg-gradient-to-br from-candy-purple-light via-candy-surface to-candy-pink-light min-h-screen`
- Card: `rounded-3xl candy-shadow-lg`
- Add a playful emoji header (owl or candy) above the form
- Error alert: `bg-candy-red-light text-candy-red border border-candy-red/20 rounded-xl`
- Submit button: large, full-width, candy-purple
- "Register" link: `text-candy-purple font-semibold`

**Step 3: Restyle register page**

Same treatment as login page.

**Step 4: Verify pages**

Check landing, login, register pages at both desktop and mobile viewport sizes.

**Step 5: Commit**

```bash
git add frontend/src/app/page.tsx frontend/src/app/(auth)/
git commit -m "feat: restyle landing and auth pages with Candy Garden theme"
```

---

### Task 5: Restyle Play Page (Main Child Hub)

**Files:**
- Modify: `frontend/src/app/(app)/play/page.tsx`

**Step 1: Replace all hardcoded colors**

Key changes:
- Page background: `bg-gradient-to-b from-candy-purple-light via-candy-surface to-candy-orange-light`
- Mascot banner: `bg-gradient-to-r from-candy-purple to-candy-pink rounded-3xl`
- Stats badges:
  - XP: `bg-candy-yellow-light text-candy-yellow` → same idea but using candy tokens
  - Streak: `bg-candy-orange-light text-candy-orange`
- Subject cards: `bg-white rounded-3xl candy-shadow hover:candy-shadow-lg hover:scale-105 transition-all duration-200`
- All `text-gray-*` → `text-candy-text` or `text-candy-text-muted`
- Stars: keep `"⭐"` and `"☆"` (universal, recognizable)
- Skeleton states: `bg-candy-purple-light animate-pulse` instead of `bg-gray-200`

**Step 2: Verify the play page**

Run: `docker compose restart frontend`
Log in as child (arthur/arthur123) and check the play page.

**Step 3: Commit**

```bash
git add frontend/src/app/(app)/play/page.tsx
git commit -m "feat: restyle play page with Candy Garden palette"
```

---

### Task 6: Restyle Subject Pages (Catalog + Lesson Tree)

**Files:**
- Modify: `frontend/src/app/(app)/subjects/page.tsx`
- Modify: `frontend/src/app/(app)/subjects/[id]/page.tsx`

**Step 1: Restyle subjects catalog**

Changes:
- All `text-gray-*` → `text-candy-text` / `text-candy-text-muted`
- Lesson count badge: `bg-candy-purple-light text-candy-purple` instead of `bg-gray-100`
- Error text: `text-candy-red`
- Cards: add `rounded-2xl candy-shadow` and `hover:candy-shadow-lg`
- Spinner: `border-candy-purple`

**Step 2: Restyle lesson tree (Duolingo-style)**

Changes:
- Background: `bg-gradient-to-b from-candy-purple-light via-candy-surface to-candy-orange-light`
- Lesson circles:
  - Active (current): `bg-gradient-to-br from-candy-purple to-candy-pink animate-[candy-glow_2s_infinite]` (replace `animate-pulse`)
  - Completed: `bg-gradient-to-br from-candy-green to-emerald-400`
  - Locked: `bg-gray-300` → `bg-candy-border`
- Connecting line: `bg-gradient-to-b from-candy-purple/40 to-transparent`
- Lesson info cards: `bg-white rounded-2xl candy-shadow`
- All `text-gray-*` → candy text tokens
- Progress bar track: `bg-candy-purple-light` instead of `bg-gray-200`
- Progress bar fill: `bg-candy-green`

**Step 3: Verify both pages**

Navigate to subjects list and a subject detail page. Check lesson tree interactions.

**Step 4: Commit**

```bash
git add frontend/src/app/(app)/subjects/
git commit -m "feat: restyle subject pages and lesson tree with Candy Garden"
```

---

### Task 7: Restyle Lesson + Exercise Pages

**Files:**
- Modify: `frontend/src/app/(app)/lessons/[id]/page.tsx`
- Modify: `frontend/src/app/(app)/exercises/[id]/page.tsx`

**Step 1: Restyle lesson detail page**

Changes:
- All `text-gray-*` → candy text tokens
- Stars: `text-candy-yellow fill-candy-yellow`
- Completed exercise card: `bg-candy-green-light border-candy-green`
- Completed circle: `bg-candy-green text-white`
- Error: `text-candy-red`
- Progress bar: candy tokens
- Empty state icon: `text-candy-border` instead of `text-gray-300`

**Step 2: Restyle exercise page**

Changes:
- Points badge: `bg-candy-yellow-light`
- Star: `text-candy-yellow fill-candy-yellow`
- Points text: `text-candy-text`
- Error: `text-candy-red`
- Spinner: `border-candy-purple`

**Step 3: Commit**

```bash
git add frontend/src/app/(app)/lessons/ frontend/src/app/(app)/exercises/
git commit -m "feat: restyle lesson and exercise pages with Candy Garden"
```

---

### Task 8: Restyle Exercise Components

**Files:**
- Modify: `frontend/src/components/exercises/MultipleChoice.tsx`
- Modify: `frontend/src/components/exercises/TrueFalse.tsx`
- Modify: `frontend/src/components/exercises/FillBlanks.tsx`
- Modify: `frontend/src/components/exercises/ImageSelection.tsx`
- Modify: `frontend/src/components/exercises/DragAndDrop.tsx`
- Modify: `frontend/src/components/exercises/ExerciseFeedback.tsx`
- Modify: `frontend/src/components/exercises/ExerciseRenderer.tsx`

**Step 1: Restyle MultipleChoice.tsx**

Replace color scheme throughout:
- Default option: `border-candy-border hover:border-candy-purple/50`
- Selected: `border-candy-purple bg-candy-purple-light ring-2 ring-candy-purple/30`
- Correct: `border-candy-green bg-candy-green-light`
- Wrong: `border-candy-red bg-candy-red-light`
- Letter badges: default `bg-candy-purple-light text-candy-purple`, selected `bg-candy-purple text-white`, correct `bg-candy-green text-white`, wrong `bg-candy-red text-white`
- Text: `text-candy-text`, `text-candy-text-muted`
- Result banner: correct `bg-candy-green-light text-candy-green`, wrong `bg-candy-red-light text-candy-red`
- Submit button: `bg-candy-purple hover:bg-candy-purple-dark text-white rounded-xl h-12 text-lg`

**Step 2: Restyle TrueFalse.tsx**

- Statement card: `bg-candy-yellow-light border-2 border-candy-yellow rounded-2xl`
- True button: `border-candy-green hover:bg-candy-green-light` with green icon bg
- False button: `border-candy-red hover:bg-candy-red-light` with red icon bg
- Selected: `border-candy-purple bg-candy-purple-light ring-4 ring-candy-purple/20`
- Correct/wrong: same candy-green/candy-red pattern
- Text: candy tokens
- Image: `rounded-2xl` with `candy-shadow`

**Step 3: Restyle FillBlanks.tsx**

- Container: `border-candy-border`
- Blank inputs: `border-2 border-candy-purple/30 rounded-lg focus:border-candy-purple focus:ring-2 focus:ring-candy-purple/20`
- Correct: `border-candy-green bg-candy-green-light`
- Wrong: `border-candy-red bg-candy-red-light`
- Hint box: `bg-candy-purple-light text-candy-text` instead of blue
- Result banner: candy tokens
- Make blank input width responsive: `w-24 sm:w-32`

**Step 4: Restyle ImageSelection.tsx**

- Image cards: `border-2 border-candy-border rounded-2xl candy-shadow hover:candy-shadow-lg`
- Selected: `border-candy-purple ring-2 ring-candy-purple/30`
- Correct overlay: `bg-candy-green/20` with `bg-candy-green` check badge
- Wrong overlay: `bg-candy-red/20` with `bg-candy-red` X badge
- Result banner: candy tokens

**Step 5: Restyle DragAndDrop.tsx**

- Items pool: `bg-candy-purple-light rounded-2xl`
- Pool title: `text-candy-text`
- Draggable items: `border-candy-border bg-white rounded-xl candy-shadow`
- Grip icon: `text-candy-text-muted`
- Target zones: `border-2 border-dashed border-candy-border bg-candy-surface rounded-2xl`
- Correct target: `border-candy-green bg-candy-green-light`
- Wrong target: `border-candy-red bg-candy-red-light`
- Result banner: candy tokens

**Step 6: Restyle ExerciseFeedback.tsx**

- Correct panel: `bg-candy-green-light border-4 border-candy-green rounded-2xl`
- Wrong panel: `bg-candy-orange-light border-4 border-candy-orange rounded-2xl`
- Correct text: `text-candy-green` for heading, `text-candy-text` for message
- Wrong text: `text-candy-orange` for heading, `text-candy-text` for message
- Continue button (correct): `bg-candy-green hover:bg-emerald-600 text-white rounded-xl`
- Retry button (wrong): `bg-candy-orange hover:bg-orange-600 text-white rounded-xl`
- Move `<style jsx>` animations to use global CSS animation classes (reference `feedback-slide-up`, `candy-shake` from globals)

**Step 7: Restyle ExerciseRenderer.tsx**

- Error: `text-candy-red bg-candy-red-light rounded-xl`
- Warning: `text-candy-orange bg-candy-orange-light rounded-xl`

**Step 8: Verify all exercise types**

Navigate through exercises and test each type (MCQ, True/False, Fill Blanks, Image Selection, Drag & Drop). Check feedback animations.

**Step 9: Commit**

```bash
git add frontend/src/components/exercises/
git commit -m "feat: restyle all exercise components with Candy Garden palette"
```

---

### Task 9: Restyle Gamification Components

**Files:**
- Modify: `frontend/src/components/gamification/Confetti.tsx`
- Modify: `frontend/src/components/gamification/LevelUp.tsx`
- Modify: `frontend/src/components/gamification/Streak.tsx`
- Modify: `frontend/src/components/gamification/StreakCelebration.tsx`
- Modify: `frontend/src/components/gamification/XPBar.tsx`
- Modify: `frontend/src/components/gamification/XPGain.tsx`
- Modify: `frontend/src/components/gamification/Badge.tsx`

**Step 1: Restyle Confetti.tsx**

- Replace colors array with candy palette: `bg-candy-purple`, `bg-candy-pink`, `bg-candy-orange`, `bg-candy-yellow`, `bg-candy-green`
- Use global `confetti-fall` animation instead of `<style jsx>`
- Add varied shapes: some `rounded-full`, some `rounded-sm`, some star-shaped via `clip-path`

**Step 2: Restyle LevelUp.tsx**

- Card gradient: `bg-gradient-to-b from-candy-yellow to-candy-orange`
- Confetti particles: candy palette hex values
- Starburst: `bg-candy-yellow/30`
- Text: `text-candy-text`, `text-white`
- Button: `bg-white text-candy-purple font-bold rounded-xl`
- Move `<style jsx>` animations to use global CSS classes

**Step 3: Restyle Streak.tsx**

- Container: `bg-gradient-to-r from-candy-orange-light to-candy-red-light rounded-2xl`
- Flame circle: `bg-candy-orange`
- Text: `text-candy-text`

**Step 4: Restyle StreakCelebration.tsx**

- Card: `bg-gradient-to-b from-candy-orange to-candy-red rounded-3xl`
- Text: `text-white`, `text-candy-orange-light`
- Dismiss button: `bg-white/20 hover:bg-white/30 rounded-xl`
- Move `<style jsx>` to global animations

**Step 5: Restyle XPBar.tsx**

- Star circle: `bg-candy-yellow`
- Star icon: `text-candy-text fill-candy-yellow`
- XP text: `text-candy-text-muted`

**Step 6: Restyle XPGain.tsx**

- Inline color: `color: "var(--candy-yellow)"` or `text-candy-yellow`
- Text shadow: candy yellow glow
- Use global `candy-float` animation instead of `<style jsx>`

**Step 7: Restyle Badge.tsx**

- Locked: `bg-candy-purple-light text-candy-text-muted`
- Earned points: `bg-candy-yellow-light text-candy-text`
- Unearned: `bg-candy-surface text-candy-text-muted`
- Lock icon color: `text-candy-text-muted`

**Step 8: Commit**

```bash
git add frontend/src/components/gamification/
git commit -m "feat: restyle gamification components with Candy Garden palette and global animations"
```

---

### Task 10: Restyle Dashboard + Admin Pages

**Files:**
- Modify: `frontend/src/app/(app)/dashboard/page.tsx`
- Modify: `frontend/src/app/(app)/admin/page.tsx`

**Step 1: Restyle dashboard**

Changes:
- Error alert: `bg-candy-red-light text-candy-red rounded-xl`
- XP stat: `text-candy-yellow`
- Streak stat: `text-candy-orange`
- Progress bar track: `bg-candy-purple-light`
- Progress bar fill: `bg-gradient-to-r from-candy-purple to-candy-pink`
- Spinner: `border-candy-purple`
- Child cards: `rounded-2xl candy-shadow`
- All gray text → candy tokens

**Step 2: Restyle admin page**

Minimal changes:
- Spinner: `border-candy-purple`
- Uses semantic tokens which are now candy-themed via globals.css
- Cards get rounder corners via the base Card component update

**Step 3: Commit**

```bash
git add frontend/src/app/(app)/dashboard/ frontend/src/app/(app)/admin/
git commit -m "feat: restyle dashboard and admin with Candy Garden palette"
```

---

### Task 11: Update CLAUDE.md with Design Guidelines

**Files:**
- Modify: `explorito/CLAUDE.md`

**Step 1: Add design guidelines section**

Add a `## Design System - Candy Garden` section to CLAUDE.md with:
- Color palette reference table
- Font: Nunito weights and usage
- Component styling rules (border-radius, shadows, touch targets)
- Mobile-first responsive patterns
- Animation naming conventions
- Do's and Don'ts for maintaining the theme

**Step 2: Commit**

```bash
git add explorito/CLAUDE.md
git commit -m "docs: add Candy Garden design guidelines to CLAUDE.md"
```

---

### Task 12: Mobile Polish + Final Verification

**Files:**
- Modify: various files as needed for mobile fixes

**Step 1: Audit all pages at 375px viewport width**

Check these screens in Chrome DevTools mobile mode:
- [ ] Landing page
- [ ] Login page
- [ ] Register page
- [ ] Play page
- [ ] Subjects catalog
- [ ] Subject detail (lesson tree)
- [ ] Lesson detail
- [ ] Exercise (each type)
- [ ] Dashboard
- [ ] Admin

**Step 2: Fix any overflow, touch target, or spacing issues found**

Common fixes:
- Ensure all interactive elements are >= 48px tall
- Ensure no horizontal overflow on 320px width
- FillBlanks inputs: responsive width
- TrueFalse images: responsive sizing
- Lesson tree nodes: responsive sizing
- Bottom nav doesn't overlap content

**Step 3: Run prettier on all modified files**

```bash
cd frontend && pnpm exec prettier --write "src/**/*.{tsx,ts,css}"
```

**Step 4: Run TypeScript check**

```bash
cd frontend && pnpm exec tsc --noEmit
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "fix: mobile polish and responsive fixes for Candy Garden theme"
```
