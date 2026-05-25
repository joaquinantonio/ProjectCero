# CeroPJ Frontend Redesign Plan

## Design Direction

CeroPJ should feel like a dark, modern music venue and studio platform. The frontend should communicate energy, creativity, and professionalism while staying simple enough for fast Django template rendering.

## Brand Feel

- Dark editorial music-site aesthetic
- Studio by day, events by night
- Artist and community focused
- Clean, mobile-first, practical
- Polished but not corporate

## Visual System

### Colours

- Background: near-black
- Panels: dark charcoal
- Accent: mint green
- Text: off-white
- Muted text: grey-blue
- Borders: subtle dark grey

### Typography

- Large expressive hero headings
- Clear section headings
- Compact metadata for dates, times, prices, and categories
- Better paragraph readability on mobile

### Components

- Page hero
- Section header
- Event card
- Artist card
- Studio service card
- Merch card
- News card
- CTA panel
- Search/filter bar
- Detail sidebar
- Form shell

## Homepage Structure

1. Hero
   - Studio by day, events by night
   - Primary CTA: View Events
   - Secondary CTA: Book Studio
   - Tertiary CTA: Enquire

2. Featured Events
   - Upcoming event cards
   - Calendar CTA
   - All events CTA

3. Studio Services
   - Featured studio services
   - Booking CTA

4. Artist Spotlight
   - Featured artists
   - Artist listing CTA

5. Merch / Drops
   - Featured merch
   - Merch listing CTA

6. News / Updates
   - Latest posts
   - News listing CTA

7. Final CTA
   - Book studio
   - Venue hire
   - General enquiry

## Navigation

Recommended primary nav:

- Home
- Events
- Studio
- Artists
- Merch
- News
- Book / Enquire

Secondary/footer links:

- About
- Contact
- Calendar
- General enquiry
- Payment enquiry
- Social links

## Implementation Order

### Phase 5B: Design System Cleanup

- Clean CSS variables
- Fix `.card-footer` selector
- Improve buttons
- Improve cards
- Improve typography
- Improve section spacing
- Improve mobile rhythm

### Phase 5C: Homepage Redesign

- Redesign hero
- Redesign section layout
- Add reusable card partials
- Improve CTA flow

### Phase 5D: Listing Pages

- Events list
- Studio list
- Artist list
- Merch list
- News list

### Phase 5E: Detail Pages

- Event detail
- Studio detail
- Artist detail
- Merch detail
- News detail

### Phase 5F: Forms

- Booking request form
- Order form
- Enquiry forms
- Success pages

## Rules

- Keep Django templates
- Avoid JavaScript-heavy redesign
- Keep performance tests passing
- Keep mobile-first layout
- Reuse existing models and view context
- Do not change database structure for redesign
- Avoid breaking existing URLs